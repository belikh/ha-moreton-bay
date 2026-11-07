"""Config flow for City of Moreton Bay."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ADDRESS,
    CONF_LAYER_TITLE,
    CONF_MODE,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL_HOURS,
    MIN_SCAN_INTERVAL_HOURS,
    MODE_ALL_LAYERS,
    MODE_SINGLE_LAYER,
    MODE_WASTE,
)

_LOGGER = logging.getLogger(__name__)

_MODE_OPTIONS: list[SelectOptionDict] = [
    {"value": MODE_ALL_LAYERS, "label": "All Datahub layers"},
    {"value": MODE_WASTE, "label": "Property waste collection days"},
    {"value": MODE_SINGLE_LAYER, "label": "Single Datahub layer"},
]

MODE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MODE): SelectSelector(
            SelectSelectorConfig(
                options=_MODE_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)

WASTE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=6): vol.All(
            int, vol.Range(min=MIN_SCAN_INTERVAL_HOURS, max=MAX_SCAN_INTERVAL_HOURS)
        ),
    }
)

SINGLE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LAYER_TITLE): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=6): vol.All(
            int, vol.Range(min=MIN_SCAN_INTERVAL_HOURS, max=MAX_SCAN_INTERVAL_HOURS)
        ),
    }
)


class MoretonBayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Moreton Bay."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the flow."""
        self._mode: str = MODE_ALL_LAYERS

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a mode."""
        if user_input is not None:
            self._mode = str(user_input[CONF_MODE])
            if self._mode == MODE_WASTE:
                return await self.async_step_waste()
            if self._mode == MODE_SINGLE_LAYER:
                return await self.async_step_single()
            return await self.async_step_all()
        return self.async_show_form(step_id="user", data_schema=MODE_SCHEMA)

    async def async_step_all(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an all-layers entry."""
        if user_input is not None:
            return self.async_create_entry(
                title="City of Moreton Bay (all layers)",
                data={CONF_MODE: MODE_ALL_LAYERS},
                options={
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, 6),
                },
            )
        return self.async_show_form(
            step_id="all",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=6): vol.All(
                        int,
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_HOURS,
                            max=MAX_SCAN_INTERVAL_HOURS,
                        ),
                    )
                }
            ),
        )

    async def async_step_waste(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a waste entry for one address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            address = str(user_input[CONF_ADDRESS]).strip()
            if not address:
                errors[CONF_ADDRESS] = "address_required"
            else:
                return self.async_create_entry(
                    title=f"Moreton Bay waste — {address}",
                    data={CONF_MODE: MODE_WASTE, CONF_ADDRESS: address.upper()},
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, 6),
                    },
                )
        return self.async_show_form(
            step_id="waste", data_schema=WASTE_SCHEMA, errors=errors
        )

    async def async_step_single(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a single-layer entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            title = str(user_input[CONF_LAYER_TITLE]).strip()
            if not title:
                errors[CONF_LAYER_TITLE] = "title_required"
            else:
                return self.async_create_entry(
                    title=f"Moreton Bay — {title}",
                    data={CONF_MODE: MODE_SINGLE_LAYER, CONF_LAYER_TITLE: title},
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, 6),
                    },
                )
        return self.async_show_form(
            step_id="single", data_schema=SINGLE_SCHEMA, errors=errors
        )
