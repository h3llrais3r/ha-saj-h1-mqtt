"""Config flow for the SAJ H1 MQTT integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_ENABLE_MQTT_DEBUG,
    CONF_SCAN_INTERVAL_BATTERY_CONTROLLER_DATA,
    CONF_SCAN_INTERVAL_BATTERY_DATA,
    CONF_SCAN_INTERVAL_CONFIG_DATA,
    CONF_SCAN_INTERVAL_INVERTER_DATA,
    CONF_SCAN_INTERVAL_REALTIME_DATA,
    CONF_SERIAL_NUMBER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): cv.string,
        vol.Required(
            CONF_SCAN_INTERVAL_REALTIME_DATA,
            default=DEFAULT_SCAN_INTERVAL.seconds,
        ): NumberSelector(
            NumberSelectorConfig(
                min=10,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="seconds",
            )
        ),
    },
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_SCAN_INTERVAL_REALTIME_DATA,
            default=DEFAULT_SCAN_INTERVAL.seconds,
        ): NumberSelector(
            NumberSelectorConfig(
                min=10,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="seconds",
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_INVERTER_DATA,
            default=0,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                step=10,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="seconds",
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_BATTERY_DATA,
            default=0,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                step=10,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="seconds",
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_BATTERY_CONTROLLER_DATA,
            default=0,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                step=10,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="seconds",
            )
        ),
        vol.Optional(
            CONF_SCAN_INTERVAL_CONFIG_DATA,
            default=0,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                step=10,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="seconds",
            )
        ),
        vol.Optional(
            CONF_ENABLE_MQTT_DEBUG,
            default=False,
        ): BooleanSelector(),
    }
)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial config flow."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SERIAL_NUMBER])
            self._abort_if_unique_id_configured()

            title = user_input[CONF_SERIAL_NUMBER]
            return self.async_create_entry(
                title=title,
                data={CONF_SERIAL_NUMBER: user_input[CONF_SERIAL_NUMBER]},
                options={
                    CONF_SCAN_INTERVAL_REALTIME_DATA: user_input[
                        CONF_SCAN_INTERVAL_REALTIME_DATA
                    ]
                },
            )

        # No config yet
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlow):
    """Handle the options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options flow."""
        if user_input is not None:
            title = self.config_entry.data[CONF_SERIAL_NUMBER]
            return self.async_create_entry(title=title, data=user_input)

        # Copy existing config_entry options into the options schema
        options_schema = self.add_suggested_values_to_schema(
            OPTIONS_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)
