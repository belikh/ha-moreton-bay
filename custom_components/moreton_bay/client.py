"""ArcGIS REST client for City of Moreton Bay Datahub.

Every endpoint here is token-free. Datahub is an ArcGIS Hub portal;
datasets are served from ``services-ap1.arcgis.com`` FeatureServers
and queried with the standard ArcGIS REST ``/query`` operation.
Licence: Creative Commons Attribution 4.0 (City of Moreton Bay).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aiohttp import ClientSession

from .const import (
    DATAHUB_CATALOGUE_URL,
    MBRC_WASTE_LAYER,
    MBRC_WASTE_URL,
)


@dataclass(frozen=True)
class LayerDefinition:
    """One published Datahub dataset."""

    title: str
    url: str
    layer: int | None = None
    description: str = ""
    categories: tuple[str, ...] = ()

    @property
    def service_url(self) -> str:
        """Return the FeatureServer URL without a trailing layer id."""
        base = self.url.rstrip("/")
        # Catalogue URLs sometimes end in /FeatureServer/<id>; strip it.
        parts = base.split("/")
        if parts and parts[-1].isdigit():
            return "/".join(parts[:-1])
        return base

    def query_url(self, layer: int | None = None) -> str:
        """Return the ArcGIS query URL for *layer* (defaults to own layer)."""
        layer_id = layer if layer is not None else (self.layer or 0)
        # If url already ends in a layer id, use it as-is.
        if self.url.rstrip("/").split("/")[-1].isdigit() and layer is None:
            return f"{self.url.rstrip('/')}/query"
        return f"{self.service_url}/{layer_id}/query"


@dataclass
class CatalogueResult:
    """Result of a catalogue fetch."""

    layers: list[LayerDefinition] = field(default_factory=list)
    fetched_at: str = ""


DYNAMIC_TITLE_SUBSTRINGS = (
    "waste collection",
    "road closure",
    "development application",
    "planned burn",
    "rail trail",
    "sandbag",
    "evacuation",
    "place of refuge",
    "of refuge",
    "traffic count",
)


def is_junk_title(title: str) -> bool:
    """Return True if a dataset is not dynamic (kept whitelist) or historical."""
    lowered = title.lower()
    if "historical" in lowered:
        return True
    return not any(token in lowered for token in DYNAMIC_TITLE_SUBSTRINGS)


def parse_catalogue(payload: dict[str, Any]) -> list[LayerDefinition]:
    """Parse an ArcGIS Hub catalogue GeoJSON payload into layers.

    Pure function (no I/O) so it can be unit-tested with fixtures.
    """
    layers: list[LayerDefinition] = []
    features = payload.get("features") or []
    for feature in features:
        props = feature.get("properties") or {}
        title = (props.get("title") or props.get("name") or "").strip()
        url = (props.get("url") or "").strip()
        if not title or not url:
            continue
        if is_junk_title(title):
            continue
        description = (props.get("snippet") or props.get("description") or "").strip()
        raw_categories = props.get("category") or props.get("categories") or []
        categories: tuple[str, ...]
        if isinstance(raw_categories, str):
            categories = (raw_categories,)
        elif isinstance(raw_categories, list):
            categories = tuple(str(c) for c in raw_categories if c)
        else:
            categories = ()
        layer_id: int | None = None
        tail = url.rstrip("/").split("/")[-1]
        if tail.isdigit():
            layer_id = int(tail)
        layers.append(
            LayerDefinition(
                title=title,
                url=url,
                layer=layer_id,
                description=description,
                categories=categories,
            )
        )
    # Deterministic order for stable entity ids.
    layers.sort(key=lambda item: item.title.lower())
    return layers


def build_where_clause(address: str) -> str:
    """Build an ArcGIS WHERE clause for an exact address match."""
    escaped = address.replace("'", "''").upper().strip()
    return f"upper(ADDRESS) = '{escaped}'"


def parse_waste_property(
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Extract the first waste property from an ArcGIS query response."""
    features = payload.get("features") or []
    if not features:
        return None
    return dict(features[0].get("attributes") or {})


class MoretonBayClient:
    """Thin async client for Datahub catalogue and FeatureServer queries."""

    def __init__(self, session: ClientSession) -> None:
        """Initialise with a shared aiohttp session."""
        self._session = session

    async def fetch_catalogue(self) -> list[LayerDefinition]:
        """Fetch and parse the Datahub dataset catalogue."""
        async with self._session.get(
            DATAHUB_CATALOGUE_URL,
            params={"limit": "1000"},
        ) as response:
            response.raise_for_status()
            payload = await response.json()
        return parse_catalogue(payload)

    async def query_layer_count(self, definition: LayerDefinition) -> int:
        """Return the feature count for one layer (best effort)."""
        payload = await self._query(
            definition.query_url(),
            {"where": "1=1", "returnCountOnly": "true"},
        )
        count = payload.get("count")
        return int(count) if isinstance(count, (int, float)) else 0

    async def query_layer_features(
        self,
        definition: LayerDefinition,
        *,
        where: str = "1=1",
        out_fields: str = "*",
        result_record_count: int = 25,
        return_geometry: bool = False,
    ) -> list[dict[str, Any]]:
        """Query attributes for features in one layer."""
        payload = await self._query(
            definition.query_url(),
            {
                "where": where,
                "outFields": out_fields,
                "returnGeometry": str(return_geometry).lower(),
                "resultRecordCount": str(result_record_count),
            },
        )
        return [
            dict(item.get("attributes") or {}) for item in payload.get("features") or []
        ]

    async def _fetch_nearby_features(
        self,
        url: str,
        layer_id: int,
        centre_latitude: float,
        centre_longitude: float,
        radius_km: float,
        out_fields: str,
    ) -> list[dict[str, Any]]:
        """Fetch features in an envelope around a coordinate (WGS84)."""
        definition = LayerDefinition(title="nearby", url=url, layer=layer_id)
        deg = radius_km / 111.0
        envelope = (
            f"{centre_longitude - deg},{centre_latitude - deg},"
            f"{centre_longitude + deg},{centre_latitude + deg}"
        )
        payload = await self._query(
            definition.query_url(),
            {
                "geometry": envelope,
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "outSR": "4326",
                "outFields": out_fields,
                "returnGeometry": "true",
                "resultRecordCount": "200",
            },
        )
        return [dict(item) for item in payload.get("features") or []]

    async def fetch_development_applications(
        self,
        centre_latitude: float,
        centre_longitude: float,
        radius_km: float,
    ) -> list[dict[str, Any]]:
        """Development applications near a coordinate (status feed)."""
        return await self._fetch_nearby_features(
            "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/MyStreet/FeatureServer/0",
            0,
            centre_latitude,
            centre_longitude,
            radius_km,
            "FORMATTED_APPLICATION_NUMBER,DESCRIPTION,STATUS_DESCRIPTION,LODGED_DATE,TYPE_DESCRIPTION",
        )

    async def fetch_road_closures(
        self,
        centre_latitude: float,
        centre_longitude: float,
        radius_km: float,
    ) -> list[dict[str, Any]]:
        """Weather-impacted road closures near a coordinate."""
        return await self._fetch_nearby_features(
            "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/RoadClosureProdView/FeatureServer/0",
            0,
            centre_latitude,
            centre_longitude,
            radius_km,
            "STATUS,REASON,ROAD,SUBURB,UPDATETIME",
        )

    async def fetch_emergency_sites(
        self,
        centre_latitude: float,
        centre_longitude: float,
        radius_km: float,
    ) -> list[dict[str, Any]]:
        """Sandbag / evacuation sites near a coordinate."""
        return await self._fetch_nearby_features(
            "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/MBRC_Sandbag_Locations_and_Evacuation_Centres_(Open)/FeatureServer/0",
            0,
            centre_latitude,
            centre_longitude,
            radius_km,
            "NAME,SUBURB,DETAILS,Status,CAPACITY,ADDRESS",
        )

    async def fetch_waste_property(self, address: str) -> dict[str, Any] | None:
        """Fetch bin day / recycle week for an exact ADDRESS value."""
        waste = LayerDefinition(
            title="Property Waste Collection Days and Recycle Weeks",
            url=f"{MBRC_WASTE_URL}/{MBRC_WASTE_LAYER}",
            layer=MBRC_WASTE_LAYER,
        )
        features = await self.query_layer_features(
            waste,
            where=build_where_clause(address),
            out_fields="ADDRESS,Bin_Day,Recycle_Week,Suburb,Road,House_No",
            result_record_count=5,
        )
        if not features:
            return None
        return features[0]

    async def _query(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        """GET an ArcGIS REST endpoint and return parsed JSON."""
        merged = dict(params)
        merged["f"] = "pjson"
        async with self._session.get(url, params=merged) as response:
            response.raise_for_status()
            return await response.json()
