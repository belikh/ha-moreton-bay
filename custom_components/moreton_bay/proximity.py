"""Proximity helpers for HA zones."""

from __future__ import annotations

import math
from typing import Any

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def count_nearby(
    features: list[dict[str, Any]],
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Count features within *radius_km* of a coordinate.

    Features are ArcGIS query results with ``geometry`` dicts in
    WGS84 when ``outSR=4326`` is requested. Returns the closest
    ``limit`` entries sorted by distance with a ``distance_km`` key.
    """
    nearby: list[dict[str, Any]] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        x = geometry.get("x")
        y = geometry.get("y")
        if x is None or y is None:
            continue
        distance = haversine_km(latitude, longitude, float(y), float(x))
        if distance <= radius_km:
            attributes = dict(feature.get("attributes") or {})
            attributes["distance_km"] = round(distance, 3)
            nearby.append(attributes)
    nearby.sort(key=lambda item: item["distance_km"])
    return nearby[:limit]
