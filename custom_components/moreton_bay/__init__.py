"""The Moreton Bay integration."""

from __future__ import annotations

from datetime import timedelta

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import LayerDefinition, MoretonBayClient
from .const import (
    CONF_ADDRESS,
    CONF_MODE,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_ZONE,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ZONE,
    DOMAIN,
    MODE_NEARBY,
    MODE_WASTE,
)
from .proximity import count_nearby

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


class MoretonBayCoordinator(DataUpdateCoordinator):
    """Coordinate all Moreton Bay updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: ClientSession,
        client: MoretonBayClient,
    ) -> None:
        """Initialise the coordinator."""
        scan_hours = entry.options.get(
            CONF_SCAN_INTERVAL,
            int(DEFAULT_SCAN_INTERVAL.total_seconds() // 3600),
        )
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(hours=float(scan_hours)),
        )
        self.entry = entry
        self.session = session
        self.client = client
        self.layers: list[LayerDefinition] = []
        self.counts: dict[str, int] = {}
        self.waste: dict | None = None
        self.nearby: list[dict] = []
        self.road_closures: list[dict] = []
        self.emergency_sites: list[dict] = []

    @property
    def zone_entity(self) -> str:
        """Return the configured zone entity id."""
        value = self.entry.options.get(CONF_ZONE, DEFAULT_ZONE)
        return str(value)

    @property
    def radius_km(self) -> float:
        """Return the configured radius in kilometres."""
        value = self.entry.options.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM)
        return float(value) if isinstance(value, (int, float)) else DEFAULT_RADIUS_KM

    @property
    def mode(self) -> str:
        """Return the configured mode."""
        return str(self.entry.options.get(CONF_MODE, ""))

    @property
    def address(self) -> str | None:
        """Return the configured waste address, if any."""
        value = self.entry.options.get(CONF_ADDRESS)
        return str(value) if value else None

    async def _async_update_data(self) -> dict:
        """Fetch catalogue, layer counts, and waste for the address."""
        self.layers = await self.client.fetch_catalogue()
        self.counts = {}
        for layer in self.layers:
            try:
                self.counts[layer.title] = await self.client.query_layer_count(layer)
            except Exception:  # noqa: BLE001 - best effort per layer
                self.counts[layer.title] = 0
        self.waste = None
        if self.address and self.mode == MODE_WASTE:
            self.waste = await self.client.fetch_waste_property(self.address)
        self.nearby = []
        self.road_closures = []
        self.emergency_sites = []
        if self.mode == MODE_NEARBY:
            zone_state = self.hass.states.get(self.zone_entity)
            if zone_state is not None:
                try:
                    latitude = float(zone_state.attributes["latitude"])
                    longitude = float(zone_state.attributes["longitude"])
                    features = await self.client.fetch_development_applications(
                        latitude, longitude, self.radius_km
                    )
                    closures = await self.client.fetch_road_closures(
                        latitude, longitude, self.radius_km
                    )
                    emergency = await self.client.fetch_emergency_sites(
                        latitude, longitude, self.radius_km
                    )
                    self.nearby = count_nearby(
                        features,
                        latitude=latitude,
                        longitude=longitude,
                        radius_km=self.radius_km,
                    )
                    self.road_closures = count_nearby(
                        closures,
                        latitude=latitude,
                        longitude=longitude,
                        radius_km=self.radius_km,
                    )
                    self.emergency_sites = count_nearby(
                        emergency,
                        latitude=latitude,
                        longitude=longitude,
                        radius_km=self.radius_km,
                    )
                except Exception:  # noqa: BLE001 - keep last known data
                    pass
        return {
            "layers": self.layers,
            "counts": self.counts,
            "waste": self.waste,
            "nearby": self.nearby,
            "road_closures": self.road_closures,
            "emergency_sites": self.emergency_sites,
        }


def _scan_interval(entry: ConfigEntry) -> timedelta:
    """Return the configured scan interval."""
    hours = entry.options.get(CONF_SCAN_INTERVAL)
    if isinstance(hours, (int, float)) and hours > 0:
        return timedelta(hours=float(hours))
    return DEFAULT_SCAN_INTERVAL


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Moreton Bay from a config entry."""
    session = async_get_clientsession(hass)
    client = MoretonBayClient(session)
    coordinator = MoretonBayCoordinator(hass, entry, session, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
