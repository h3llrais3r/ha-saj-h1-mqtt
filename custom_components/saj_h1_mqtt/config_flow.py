"""Config flow for the SAJ H1 MQTT integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.mqtt import DOMAIN as MQTT_DOMAIN
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
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ENABLE_ACCURATE_REALTIME_POWER_DATA,
    CONF_ENABLE_MODBUS_DEBUG,
    CONF_ENABLE_MQTT_DEBUG,
    CONF_ENABLE_SERIAL_NUMBER_PREFIX,
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL_BATTERY_CONTROLLER_DATA,
    CONF_SCAN_INTERVAL_BATTERY_DATA,
    CONF_SCAN_INTERVAL_CONFIG_DATA,
    CONF_SCAN_INTERVAL_INVERTER_DATA,
    CONF_SCAN_INTERVAL_REALTIME_DATA,
    CONF_SERIAL_NUMBER,
    DEFAULT_MODBUS_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROTOCOL_MODBUS,
    PROTOCOL_MQTT,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): cv.string,
        vol.Required(CONF_PROTOCOL, default=PROTOCOL_MQTT): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=PROTOCOL_MQTT,
                        label="MQTT",
                    ),
                    SelectOptionDict(
                        value=PROTOCOL_MODBUS,
                        label="Modbus",
                    ),
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
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
            CONF_ENABLE_SERIAL_NUMBER_PREFIX,
            default=False,
        ): BooleanSelector(),
    }
)

MQTT_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_ENABLE_MQTT_DEBUG,
            default=False,
        ): BooleanSelector(),
    }
)

MODBUS_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MODBUS_HOST): cv.string,
        vol.Required(CONF_MODBUS_PORT, default=DEFAULT_MODBUS_PORT): cv.positive_int,
        vol.Optional(
            CONF_ENABLE_MODBUS_DEBUG,
            default=False,
        ): BooleanSelector(),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PROTOCOL, default=PROTOCOL_MQTT): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=PROTOCOL_MQTT,
                        label="MQTT",
                    ),
                    SelectOptionDict(
                        value=PROTOCOL_MODBUS,
                        label="Modbus",
                    ),
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
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
            CONF_ENABLE_SERIAL_NUMBER_PREFIX,
            default=False,
        ): BooleanSelector(),
        vol.Optional(
            CONF_ENABLE_ACCURATE_REALTIME_POWER_DATA,
            default=False,
        ): BooleanSelector(),
    }
)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 2
    _serial_number: str | None = None
    _protocol: str | None = None
    _scan_interval: int | None = None
    _enable_prefix: bool | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial config flow."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SERIAL_NUMBER])
            self._abort_if_unique_id_configured()

            self._serial_number = user_input[CONF_SERIAL_NUMBER]
            self._protocol = user_input[CONF_PROTOCOL]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL_REALTIME_DATA]
            self._enable_prefix = user_input[CONF_ENABLE_SERIAL_NUMBER_PREFIX]

            if self._protocol == PROTOCOL_MQTT:
                # Check is MQTT is set up
                if not self.hass.config_entries.async_entries(MQTT_DOMAIN):
                    return self.async_abort(reason="mqtt_required")

                return await self.async_step_mqtt_config()

            if self._protocol == PROTOCOL_MODBUS:
                return await self.async_step_modbus_config()

        # No config yet
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    async def async_step_mqtt_config(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial mqtt config flow."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._serial_number,
                data={
                    CONF_SERIAL_NUMBER: self._serial_number,
                },
                options={
                    CONF_PROTOCOL: self._protocol,
                    CONF_SCAN_INTERVAL_REALTIME_DATA: self._scan_interval,
                    CONF_ENABLE_SERIAL_NUMBER_PREFIX: self._enable_prefix,
                    CONF_ENABLE_MQTT_DEBUG: user_input[CONF_ENABLE_MQTT_DEBUG],
                },
            )

        # No config yet
        return self.async_show_form(
            step_id="mqtt_config", data_schema=MQTT_CONFIG_SCHEMA
        )

    async def async_step_modbus_config(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial modbus config flow."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._serial_number,
                data={
                    CONF_SERIAL_NUMBER: self._serial_number,
                },
                options={
                    CONF_PROTOCOL: self._protocol,
                    CONF_SCAN_INTERVAL_REALTIME_DATA: self._scan_interval,
                    CONF_ENABLE_SERIAL_NUMBER_PREFIX: self._enable_prefix,
                    CONF_MODBUS_HOST: user_input[CONF_MODBUS_HOST],
                    CONF_MODBUS_PORT: user_input[CONF_MODBUS_PORT],
                    CONF_ENABLE_MODBUS_DEBUG: user_input[CONF_ENABLE_MODBUS_DEBUG],
                },
            )

        # No config yet
        return self.async_show_form(
            step_id="modbus_config", data_schema=MODBUS_CONFIG_SCHEMA
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handle the options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self._data: dict[str, Any] = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options flow."""
        if user_input is not None:
            self._data.update(user_input)
            protocol = user_input[CONF_PROTOCOL]

            if protocol == PROTOCOL_MQTT:
                return await self.async_step_mqtt_options()

            if protocol == PROTOCOL_MODBUS:
                return await self.async_step_modbus_options()

        # Copy existing config_entry options into the options schema
        options_schema = self.add_suggested_values_to_schema(
            OPTIONS_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)

    async def async_step_mqtt_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the mqtt options flow."""
        if user_input is not None:
            self._data.update(user_input)
            title = self.config_entry.data[CONF_SERIAL_NUMBER]
            return self.async_create_entry(title=title, data=self._data)

        # Copy existing config_entry options into the mqtt config schema
        mqtt_config_schema = self.add_suggested_values_to_schema(
            MQTT_CONFIG_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(
            step_id="mqtt_options", data_schema=mqtt_config_schema
        )

    async def async_step_modbus_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the modbus options flow."""
        if user_input is not None:
            self._data.update(user_input)
            title = self.config_entry.data[CONF_SERIAL_NUMBER]
            return self.async_create_entry(title=title, data=self._data)

        # Copy existing config_entry options into the modbus config schema
        modbus_config_schema = self.add_suggested_values_to_schema(
            MODBUS_CONFIG_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(
            step_id="modbus_options", data_schema=modbus_config_schema
        )
