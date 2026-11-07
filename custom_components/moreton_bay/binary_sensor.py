"""Binary sensors for City of Moreton Bay."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MoretonBayCoordinator
from .const import MODE_WASTE
from .waste import put_out_tonight


class MoretonBayWastePutOutTonightSensor(
    CoordinatorEntity[MoretonBayCoordinator], BinarySensorEntity
):
    """True when bins go out tonight for tomorrow's collection."""

    _attr_has_entity_name = True
    _attr_name = "Put bins out tonight"
    _attr_unique_id = "moreton_bay_waste_put_out_tonight"

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        """Return whether bins go out tonight."""
        waste = self.coordinator.waste or {}
        bin_day = str(waste.get("Bin_Day") or "")
        try:
            from zoneinfo import ZoneInfo

            today = datetime.now(ZoneInfo("Australia/Brisbane")).date()
        except Exception:  # noqa: BLE001 - fallback to UTC date
            today = datetime.now().date()
        return put_out_tonight(bin_day, today)

    @property
    def extra_state_attributes(self) -> dict:
        """Return waste details."""
        waste = self.coordinator.waste or {}
        return {
            "address": waste.get("ADDRESS"),
            "bin_day": waste.get("Bin_Day"),
            "recycle_week": waste.get("Recycle_Week"),
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Moreton Bay binary sensors from a config entry."""
    coordinator: MoretonBayCoordinator = hass.data["moreton_bay"][entry.entry_id]
    if coordinator.mode != MODE_WASTE:
        return
    async_add_entities([MoretonBayWastePutOutTonightSensor(coordinator)])
