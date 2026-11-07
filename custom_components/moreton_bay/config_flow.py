"""Config flow for City of Moreton Bay — single mode."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
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

SETUP_SCHEMA = vol.Schema(
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
        vol.Optional(CONF_ADDRESS, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
    }
)


class MoretonBayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the single-mode config flow for Moreton Bay."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the single setup step."""
        if user_input is not None:
            zone = str(user_input.get(CONF_ZONE) or DEFAULT_ZONE)
            radius = float(user_input.get(CONF_RADIUS_KM) or DEFAULT_RADIUS_KM)
            address = str(user_input.get(CONF_ADDRESS) or "").strip()
            data: dict[str, Any] = {CONF_ZONE: zone, CONF_RADIUS_KM: radius}
            if address:
                data[CONF_ADDRESS] = address.upper()
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, 6)
            try:
                scan_interval = int(float(scan_interval))
            except TypeError, ValueError:
                scan_interval = 6
            return self.async_create_entry(
                title=f"City of Moreton Bay — {zone}",
                data=data,
                options={CONF_SCAN_INTERVAL: scan_interval},
            )
        return self.async_show_form(step_id="user", data_schema=SETUP_SCHEMA)


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
