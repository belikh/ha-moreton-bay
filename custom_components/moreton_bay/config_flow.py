"""Config flow for City of Moreton Bay — single mode with guided waste lookup."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_ADDRESS,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_ZONE,
    DEFAULT_RADIUS_KM,
    DEFAULT_ZONE,
    DOMAIN,
    MAX_SCAN_INTERVAL_HOURS,
    MIN_SCAN_INTERVAL_HOURS,
)

_LOGGER = logging.getLogger(__name__)

WASTE_QUERY_URL = (
    "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/"
    "MBRC_Waste/FeatureServer/0/query"
)


def _select(options: list[str]) -> SelectSelectorConfig:
    """Build a dropdown config for *options* (capped for HA)."""
    seen: list[str] = []
    for value in options:
        if value and value not in seen:
            seen.append(value)
    return SelectSelectorConfig(
        options=seen[:500],
        mode=SelectSelectorMode.DROPDOWN,
    )


async def _fetch_distinct(hass: Any, where: str, field: str) -> list[str]:
    """Fetch distinct values for *field* from the waste layer."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            WASTE_QUERY_URL,
            params={
                "where": where,
                "outFields": field,
                "returnGeometry": "false",
                "returnDistinctValues": "true",
                "orderByFields": field,
                "resultRecordCount": "500",
                "f": "pjson",
            },
        ) as response:
            response.raise_for_status()
            payload = await response.json()
        values = [
            str(item.get("attributes", {}).get(field) or "").strip()
            for item in payload.get("features") or []
        ]
        return [value for value in values if value]
    except Exception:  # noqa: BLE001 - wizard falls back to manual entry
        return []


class MoretonBayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the single-mode config flow for Moreton Bay."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the wizard state."""
        self._zone = DEFAULT_ZONE
        self._radius = DEFAULT_RADIUS_KM
        self._scan_interval = 6
        self._address = ""
        self._suburb = ""
        self._street = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: zone and radius (zone drives waste fallback + status)."""
        schema = vol.Schema(
            {
                vol.Required(CONF_ZONE, default=DEFAULT_ZONE): EntitySelector(
                    EntitySelectorConfig(domain="zone", multiple=False)
                ),
                vol.Required(CONF_RADIUS_KM, default=DEFAULT_RADIUS_KM): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=50.0,
                        step=0.1,
                        unit_of_measurement="km",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=6): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_HOURS,
                        max=MAX_SCAN_INTERVAL_HOURS,
                        step=1.0,
                        unit_of_measurement="hours",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        if user_input is not None:
            self._zone = str(user_input.get(CONF_ZONE) or DEFAULT_ZONE)
            self._radius = float(user_input.get(CONF_RADIUS_KM) or DEFAULT_RADIUS_KM)
            raw_interval = user_input.get(CONF_SCAN_INTERVAL, 6)
            try:
                self._scan_interval = int(float(raw_interval))
            except TypeError, ValueError:
                self._scan_interval = 6
            return await self.async_step_suburb()
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_suburb(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: pick a suburb (guided) or type a full address."""
        if user_input is not None:
            manual = str(user_input.get(CONF_ADDRESS) or "").strip()
            if manual:
                self._address = manual.upper()
                return await self.async_step_confirm()
            self._suburb = str(user_input.get("suburb") or "")
            if self._suburb:
                return await self.async_step_street()
        suburbs = await _fetch_distinct(self.hass, "1=1", "Suburb")
        schema = vol.Schema(
            {
                vol.Optional("suburb"): SelectSelector(_select(suburbs)),
                vol.Optional(CONF_ADDRESS): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(step_id="suburb", data_schema=schema)

    async def async_step_street(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 3: pick a street within the suburb."""
        if user_input is not None:
            manual = str(user_input.get(CONF_ADDRESS) or "").strip()
            if manual:
                self._address = manual.upper()
                return await self.async_step_confirm()
            self._street = str(user_input.get("street") or "")
            if self._street:
                return await self.async_step_house()
        where = f"Suburb='{self._suburb.replace(chr(39), chr(39) * 2)}'"
        streets = await _fetch_distinct(self.hass, where, "Road")
        schema = vol.Schema(
            {
                vol.Required("street"): SelectSelector(_select(streets)),
                vol.Optional(CONF_ADDRESS): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(step_id="street", data_schema=schema)

    async def async_step_house(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 4: pick a house number within the street."""
        if user_input is not None:
            manual = str(user_input.get(CONF_ADDRESS) or "").strip()
            if manual:
                self._address = manual.upper()
                return await self.async_step_confirm()
            house = str(user_input.get("house") or "").strip()
            if house:
                self._address = f"{house} {self._street} {self._suburb}"
                return await self.async_step_confirm()
        where = (
            f"Suburb='{self._suburb.replace(chr(39), chr(39) * 2)}' "
            f"AND Road='{self._street.replace(chr(39), chr(39) * 2)}'"
        )
        houses = await _fetch_distinct(self.hass, where, "House_No")
        schema = vol.Schema(
            {
                vol.Required("house"): SelectSelector(_select(houses)),
                vol.Optional(CONF_ADDRESS): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(step_id="house", data_schema=schema)

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 5: confirm the matched council address (or leave blank for zone)."""
        if user_input is not None:
            address = str(user_input.get(CONF_ADDRESS) or "").strip()
            data: dict[str, Any] = {
                CONF_ZONE: self._zone,
                CONF_RADIUS_KM: self._radius,
            }
            if address:
                data[CONF_ADDRESS] = address.upper()
            elif self._address:
                data[CONF_ADDRESS] = self._address.upper()
            return self.async_create_entry(
                title=f"City of Moreton Bay — {self._zone}",
                data=data,
                options={CONF_SCAN_INTERVAL: self._scan_interval},
            )
        schema = vol.Schema(
            {
                vol.Optional(CONF_ADDRESS, default=self._address): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                )
            }
        )
        return self.async_show_form(step_id="confirm", data_schema=schema)


class MoretonBayOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Moreton Bay."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialise the options flow."""
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, 6)
            try:
                scan_interval = int(float(scan_interval))
            except TypeError, ValueError:
                pass
            else:
                user_input = {**user_input, CONF_SCAN_INTERVAL: scan_interval}
            return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self._entry.options.get(CONF_SCAN_INTERVAL, 6),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_HOURS,
                        max=MAX_SCAN_INTERVAL_HOURS,
                        step=1.0,
                        unit_of_measurement="hours",
                        mode=NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


def async_get_options_flow(
    entry: config_entries.ConfigEntry,
) -> MoretonBayOptionsFlow:
    """Return the options flow handler."""
    return MoretonBayOptionsFlow(entry)
