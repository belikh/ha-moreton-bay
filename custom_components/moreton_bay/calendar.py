"""Calendar entity for Moreton Bay waste collections."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MoretonBayCoordinator
from .const import DOMAIN, MODE_WASTE
from .waste import is_recycle_week, next_collection_date

EPOCH = date(2026, 1, 5)


class MoretonBayCollectionsCalendar(
    CoordinatorEntity[MoretonBayCoordinator], CalendarEntity
):
    """Calendar of general, recycling, and organics collections."""

    _attr_has_entity_name = True
    _attr_name = "Collections"
    _attr_unique_id = "moreton_bay_collections_calendar"
    _attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, DOMAIN)},
        name="City of Moreton Bay",
        manufacturer="belikh",
        model="Moreton Bay Integration",
        configuration_url="https://github.com/belikh/ha-moreton-bay",
    )

    def __init__(self, coordinator: MoretonBayCoordinator) -> None:
        """Initialise the calendar entity."""
        super().__init__(coordinator)

    @property
    def active(self) -> bool:
        """Return whether any collection happens tomorrow."""
        return False

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return upcoming collection events (next 4 weeks)."""
        waste = self.coordinator.waste or {}
        bin_day = str(waste.get("Bin_Day") or "")
        recycle_week = str(waste.get("Recycle_Week") or "")
        if not bin_day:
            return []
        events: list[CalendarEvent] = []
        cursor = start_date.date()
        end = end_date.date()
        while cursor <= end:
            nxt = next_collection_date(bin_day, cursor)
            if nxt is None or nxt > end:
                break
            is_recycle = is_recycle_week(recycle_week, nxt, EPOCH)
            summary = "General waste" + (
                " + recycling" if is_recycle else " + organics"
            )
            events.append(
                CalendarEvent(
                    summary=summary,
                    start=nxt,
                    end=nxt + timedelta(days=1),
                    description=f"Bin day {bin_day.lower()} ({recycle_week})",
                )
            )
            cursor = nxt + timedelta(days=7)
        return events


async def async_setup_entry(
    hass: HomeAssistant,
    entry: object,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Moreton Bay calendar."""
    assert hasattr(entry, "entry_id")
    coordinator: MoretonBayCoordinator = hass.data[DOMAIN][entry.entry_id]  # type: ignore[index]
    if coordinator.mode != MODE_WASTE:
        return
    async_add_entities([MoretonBayCollectionsCalendar(coordinator)])
