"""Sensors for City of Moreton Bay."""

from __future__ import annotations

from datetime import UTC, date, datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MoretonBayCoordinator
from .const import DOMAIN
from .waste import collection_type, next_collection_date, next_recycle_date

EPOCH = date(2026, 1, 5)


class MoretonBayLayerSensor(CoordinatorEntity[MoretonBayCoordinator], SensorEntity):
    """Sensor exposing the feature count for one Datahub layer."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MoretonBayCoordinator,
        layer_title: str,
        source_url: str,
    ) -> None:
        """Initialise with the layer title and source URL."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="City of Moreton Bay",
            manufacturer="belikh",
            model="Moreton Bay Integration",
            configuration_url="https://github.com/belikh/ha-moreton-bay",
        )
        self._layer_title = layer_title
        self._source_url = source_url
        slug = layer_title.lower().replace(" ", "_")
        self._attr_unique_id = f"{layer_title}_{slug}"
        self._attr_name = layer_title
        self._attr_native_unit_of_measurement = "features"

    @property
    def native_value(self) -> int | None:
        """Return the feature count for this layer."""
        return self.coordinator.counts.get(self._layer_title)

    @property
    def extra_state_attributes(self) -> dict:
        """Return layer metadata."""
        return {
            "layer_title": self._layer_title,
            "source_url": self._source_url,
            "feature_count": self.coordinator.counts.get(self._layer_title),
        }


class MoretonBayWasteNextCollectionSensor(
    CoordinatorEntity[MoretonBayCoordinator], SensorEntity
):
    """Sensor for the next general bin collection date."""

    _attr_has_entity_name = True
    _attr_device_class = None
    _attr_name = "Next bin collection"
    _attr_unique_id = "moreton_bay_waste_next_collection"

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the waste sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="City of Moreton Bay",
            manufacturer="belikh",
            model="Moreton Bay Integration",
            configuration_url="https://github.com/belikh/ha-moreton-bay",
        )

    @property
    def native_value(self) -> str | None:
        """Return the next collection date as ISO text."""
        waste = self.coordinator.waste
        if waste is None:
            return "Not found — check address"
        bin_day = str(waste.get("Bin_Day") or "")
        today = self._today()
        nxt = next_collection_date(bin_day, today)
        return nxt.isoformat() if nxt else None

    @property
    def extra_state_attributes(self) -> dict:
        """Return waste details."""
        waste = self.coordinator.waste or {}
        today = self._today()
        bin_day = str(waste.get("Bin_Day") or "")
        recycle_week = str(waste.get("Recycle_Week") or "")
        recycle_date = next_recycle_date(bin_day, recycle_week, today)
        return {
            "address": waste.get("ADDRESS"),
            "bin_day": waste.get("Bin_Day"),
            "recycle_week": waste.get("Recycle_Week"),
            "suburb": waste.get("Suburb"),
            "collection_type_next": collection_type(bin_day, recycle_week, today),
            "next_recycle_date": recycle_date.isoformat() if recycle_date else None,
        }

    @staticmethod
    def _today() -> date:
        """Return today in Brisbane time."""
        try:
            from zoneinfo import ZoneInfo

            return datetime.now(ZoneInfo("Australia/Brisbane")).date()
        except Exception:  # noqa: BLE001 - fallback to UTC date
            return datetime.now(UTC).date()


class MoretonBayWasteRecycleSensor(
    CoordinatorEntity[MoretonBayCoordinator], SensorEntity
):
    """Sensor for the next recycling collection date."""

    _attr_has_entity_name = True
    _attr_name = "Next recycling collection"
    _attr_unique_id = "moreton_bay_waste_next_recycle"

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the recycle sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="City of Moreton Bay",
            manufacturer="belikh",
            model="Moreton Bay Integration",
            configuration_url="https://github.com/belikh/ha-moreton-bay",
        )

    @property
    def native_value(self) -> str | None:
        """Return the next recycling date as ISO text."""
        waste = self.coordinator.waste
        if waste is None:
            return "Not found — check address"
        bin_day = str(waste.get("Bin_Day") or "")
        recycle_week = str(waste.get("Recycle_Week") or "")
        try:
            from zoneinfo import ZoneInfo

            today = datetime.now(ZoneInfo("Australia/Brisbane")).date()
        except Exception:  # noqa: BLE001 - fallback to UTC date
            today = datetime.now(UTC).date()
        nxt = next_recycle_date(bin_day, recycle_week, today)
        return nxt.isoformat() if nxt else None

    @property
    def extra_state_attributes(self) -> dict:
        """Return recycle details."""
        waste = self.coordinator.waste or {}
        return {
            "address": waste.get("ADDRESS"),
            "bin_day": waste.get("Bin_Day"),
            "recycle_week": waste.get("Recycle_Week"),
        }


class MoretonBayDevAppStatusSensor(
    CoordinatorEntity[MoretonBayCoordinator], SensorEntity
):
    """Status of the nearest development application."""

    _attr_has_entity_name = True
    _attr_name = "Development application (nearest)"
    _attr_unique_id = "moreton_bay_dev_app_status"

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the status sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="City of Moreton Bay",
            manufacturer="belikh",
            model="Moreton Bay Integration",
            configuration_url="https://github.com/belikh/ha-moreton-bay",
        )

    @property
    def native_value(self) -> str | None:
        """Return the nearest application's status."""
        nearby = self.coordinator.nearby
        if not nearby:
            return "None nearby"
        return str(nearby[0].get("STATUS_DESCRIPTION") or "Unknown")

    @property
    def extra_state_attributes(self) -> dict:
        """Return the nearest application details."""
        nearby = self.coordinator.nearby
        if not nearby:
            return {"count": 0, "radius_km": self.coordinator.radius_km}
        nearest = nearby[0]
        return {
            "count": len(nearby),
            "radius_km": self.coordinator.radius_km,
            "application": nearest.get("FORMATTED_APPLICATION_NUMBER"),
            "description": nearest.get("DESCRIPTION"),
            "lodged_date": nearest.get("LODGED_DATE"),
            "distance_km": nearest.get("distance_km"),
        }


class MoretonBayRoadClosureStatusSensor(
    CoordinatorEntity[MoretonBayCoordinator], SensorEntity
):
    """Status of the nearest weather-impacted road closure."""

    _attr_has_entity_name = True
    _attr_name = "Road closure (nearest)"
    _attr_unique_id = "moreton_bay_road_closure_status"

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the status sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="City of Moreton Bay",
            manufacturer="belikh",
            model="Moreton Bay Integration",
            configuration_url="https://github.com/belikh/ha-moreton-bay",
        )

    @property
    def native_value(self) -> str | None:
        """Return the nearest closure status."""
        closures = self.coordinator.road_closures
        if not closures:
            return "None nearby"
        return str(closures[0].get("STATUS") or "Unknown")

    @property
    def extra_state_attributes(self) -> dict:
        """Return the nearest closure details."""
        closures = self.coordinator.road_closures
        if not closures:
            return {"radius_km": self.coordinator.radius_km}
        nearest = closures[0]
        return {
            "radius_km": self.coordinator.radius_km,
            "road": nearest.get("ROAD"),
            "reason": nearest.get("REASON"),
            "suburb": nearest.get("SUBURB"),
            "distance_km": nearest.get("distance_km"),
        }


class MoretonBayEmergencyStatusSensor(
    CoordinatorEntity[MoretonBayCoordinator], SensorEntity
):
    """Status of the nearest sandbag / evacuation site."""

    _attr_has_entity_name = True
    _attr_name = "Emergency site (nearest)"
    _attr_unique_id = "moreton_bay_emergency_status"

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the status sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="City of Moreton Bay",
            manufacturer="belikh",
            model="Moreton Bay Integration",
            configuration_url="https://github.com/belikh/ha-moreton-bay",
        )

    @property
    def native_value(self) -> str | None:
        """Return the nearest emergency site status."""
        sites = self.coordinator.emergency_sites
        if not sites:
            return "None nearby"
        return str(sites[0].get("Status") or "Unknown")

    @property
    def extra_state_attributes(self) -> dict:
        """Return the nearest emergency site details."""
        sites = self.coordinator.emergency_sites
        if not sites:
            return {"radius_km": self.coordinator.radius_km}
        nearest = sites[0]
        return {
            "radius_km": self.coordinator.radius_km,
            "name": nearest.get("NAME"),
            "address": nearest.get("ADDRESS"),
            "details": nearest.get("DETAILS"),
            "distance_km": nearest.get("distance_km"),
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Moreton Bay sensors from a config entry."""
    coordinator: MoretonBayCoordinator = hass.data["moreton_bay"][entry.entry_id]
    entities: list[SensorEntity] = []
    for layer in coordinator.layers:
        entities.append(MoretonBayLayerSensor(coordinator, layer.title, layer.url))
    if True:  # single mode
        entities.append(MoretonBayWasteNextCollectionSensor(coordinator))
        entities.append(MoretonBayWasteRecycleSensor(coordinator))
    if True:  # single mode (nearby)
        entities.append(MoretonBayDevAppStatusSensor(coordinator))
        entities.append(MoretonBayRoadClosureStatusSensor(coordinator))
        entities.append(MoretonBayEmergencyStatusSensor(coordinator))
    async_add_entities(entities)
