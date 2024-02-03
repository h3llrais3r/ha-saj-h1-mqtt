"""Config flow for SAJ MQTT integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_ENABLE_BATTERY_CONTROLLER,
    CONF_ENABLE_BATTERY_INFO,
    CONF_ENABLE_CONFIG,
    CONF_ENABLE_INVERTER_INFO,
    CONF_ENABLE_MQTT_DEBUG,
    CONF_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_BATTERY_CONTROLLER,
    CONF_SCAN_INTERVAL_BATTERY_INFO,
    CONF_SCAN_INTERVAL_CONFIG,
    CONF_SCAN_INTERVAL_INVERTER_INFO,
    CONF_SERIAL_NUMBER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): cv.string,
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=DEFAULT_SCAN_INTERVAL.seconds,
        ): NumberSelector(
            NumberSelectorConfig(
                min=10, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_INVERTER_INFO,
            default=-1,
        ): NumberSelector(
            NumberSelectorConfig(
                min=-1, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_BATTERY_INFO,
            default=-1,
        ): NumberSelector(
            NumberSelectorConfig(
                min=-1, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_BATTERY_CONTROLLER,
            default=-1,
        ): NumberSelector(
            NumberSelectorConfig(
                min=-1, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_CONFIG,
            default=-1,
        ): NumberSelector(
            NumberSelectorConfig(
                min=-1, mode=NumberSelectorMode.BOX, unit_of_measurement="seconds"
            )
        ),
        vol.Optional(
            CONF_ENABLE_MQTT_DEBUG,
            default=False,
        ): BooleanSelector(),
    },
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAJ MQTT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        await self.async_set_unique_id(user_input[CONF_SERIAL_NUMBER])
        self._abort_if_unique_id_configured()

        if not errors:
            return self.async_create_entry(title="SAJ MQTT", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
