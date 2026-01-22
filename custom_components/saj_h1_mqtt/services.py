"""Services for the SAJ H1 MQTT integration."""

from __future__ import annotations

from datetime import datetime
from struct import unpack_from
from zoneinfo import ZoneInfo

import voluptuous as vol

from homeassistant import core
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import ConfigEntrySelector

from .const import (
    ATTR_CONFIG_ENTRY,
    ATTR_REGISTER,
    ATTR_REGISTER_FORMAT,
    ATTR_REGISTER_SIZE,
    ATTR_REGISTER_VALUE,
    DOMAIN,
    LOGGER,
    MODBUS_REG_INVERTER_TIME_READ,
    MODBUS_REG_INVERTER_TIME_WRITE,
    SERVICE_READ_REGISTER,
    SERVICE_READ_REGISTERS,
    SERVICE_REFRESH_BATTERY_CONTROLLER_DATA,
    SERVICE_REFRESH_BATTERY_DATA,
    SERVICE_REFRESH_CONFIG_DATA,
    SERVICE_REFRESH_INVERTER_DATA,
    SERVICE_SYNC_INVERTER_TIME,
    SERVICE_WRITE_REGISTER,
)
from .types import SajH1MqttConfigEntry


async def read_register(call: ServiceCall) -> core.ServiceResponse:
    """Read a single register from the inverter."""
    LOGGER.debug("Reading register")
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    mqtt_client = entry.runtime_data.mqtt_client
    attr_register: str = call.data.get(ATTR_REGISTER)
    attr_register_format: str | None = call.data.get(ATTR_REGISTER_FORMAT)

    # Validate input
    try:
        if attr_register.startswith("0x"):
            register_start = int(attr_register, 16)
        else:
            register_start = int(attr_register)
    except ValueError as e:
        LOGGER.error(f"Invalid register: {attr_register}")
        raise ServiceValidationError("Invalid register", DOMAIN) from e
    if attr_register_format and not attr_register_format.startswith(">"):
        msg = f"Invalid register format: {attr_register_format}"
        LOGGER.error(msg)
        raise ServiceValidationError("Invalid register format")

    # Read 1 register
    content = await mqtt_client.read_registers(register_start, 1)
    if content is None:
        LOGGER.error("Failed to read register")
        raise ServiceValidationError("Failed to read register")

    # Return response (format if needed, otherwise return bytes)
    if attr_register_format:
        (result,) = unpack_from(attr_register_format, content, 0)
        return {"value": str(result)}
    return {"value": ":".join(f"{b:02x}" for b in content)}


async def read_registers(call: ServiceCall) -> core.ServiceResponse:
    """Read multiple registers from the inverter."""
    LOGGER.debug("Reading registers")
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    mqtt_client = entry.runtime_data.mqtt_client
    attr_register: str = call.data.get(ATTR_REGISTER)
    attr_register_size: str = call.data.get(ATTR_REGISTER_SIZE)
    attr_register_format: str | None = call.data.get(ATTR_REGISTER_FORMAT)

    # Validate input
    try:
        if attr_register.startswith("0x"):
            register_start = int(attr_register, 16)
        else:
            register_start = int(attr_register)
    except ValueError as e:
        LOGGER.error(f"Invalid register: {attr_register}")
        raise ServiceValidationError("Invalid register", DOMAIN) from e
    try:
        if attr_register_size.startswith("0x"):
            register_size = int(attr_register_size, 16)
        else:
            register_size = int(attr_register_size)
    except ValueError as e:
        LOGGER.error(f"Invalid register size: {attr_register_size}")
        raise ServiceValidationError("Invalid register size") from e
    if attr_register_format and not attr_register_format.startswith(">"):
        msg = f"Invalid register format: {attr_register_format}"
        LOGGER.error(msg)
        raise ServiceValidationError("Invalid register format")

    # Read registers
    content = await mqtt_client.read_registers(register_start, register_size)
    if content is None:
        LOGGER.error("Failed to read registers")
        raise ServiceValidationError("Failed to read registers")

    # Return response (format if needed, otherwise return bytes)
    if attr_register_format:
        results = unpack_from(attr_register_format, content, 0)
        return {"values": [str(r) for r in results]}
    return {"values": ":".join(f"{b:02x}" for b in content)}


async def write_register(call: ServiceCall) -> None:
    """Write a single register to the inverter."""
    LOGGER.debug("Writing register")
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    mqtt_client = entry.runtime_data.mqtt_client
    attr_register: str = call.data.get(ATTR_REGISTER)
    attr_register_value: str = call.data.get(ATTR_REGISTER_VALUE)

    # Validate input
    try:
        if attr_register.startswith("0x"):
            register = int(attr_register, 16)
        else:
            register = int(attr_register)
    except ValueError as e:
        LOGGER.error(f"Invalid register: {attr_register}")
        raise ServiceValidationError("Invalid register") from e
    try:
        if attr_register_value.startswith("0x"):
            value = int(attr_register_value, 16)
        else:
            value = int(attr_register_value)
    except ValueError as e:
        LOGGER.error(f"Invalid register value: {attr_register_value}")
        raise ServiceValidationError("Invalid register value") from e

    # Write register
    await mqtt_client.write_register(register, value)


async def refresh_inverter_data(call: ServiceCall) -> None:
    """Refresh inverter data."""
    # Only refresh when coordinator is enabled
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    coordinator = entry.runtime_data.coordinator_inverter_data
    if coordinator:
        LOGGER.debug("Refreshing inverter data")
        await coordinator.async_request_refresh()


async def refresh_battery_data(call: ServiceCall) -> None:
    """Refresh battery data."""
    # Only refresh when coordinator is enabled
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    coordinator = entry.runtime_data.coordinator_battery_data
    if coordinator:
        LOGGER.debug("Refreshing battery data")
        await coordinator.async_request_refresh()


async def refresh_battery_controller_data(call: ServiceCall) -> None:
    """Refresh battery controller data."""
    # Only refresh when coordinator is enabled
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    coordinator = entry.runtime_data.coordinator_battery_controller_data
    if coordinator:
        LOGGER.debug("Refreshing battery controller data")
        await coordinator.async_request_refresh()


async def refresh_config_data(call: ServiceCall) -> None:
    """Refresh config data."""
    # Only refresh when coordinator is enabled
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    coordinator = entry.runtime_data.coordinator_config_data
    if coordinator:
        LOGGER.debug("Refreshing config data")
        await coordinator.async_request_refresh()


async def sync_inverter_time(call: ServiceCall) -> core.ServiceResponse:
    """Sync inverter time with local time."""
    LOGGER.debug("Syncing inverter time")
    entry = _get_config_entry(call.hass, call.data.get(ATTR_CONFIG_ENTRY))
    mqtt_client = entry.runtime_data.mqtt_client

    # Get current inverter time
    content = await mqtt_client.read_registers(MODBUS_REG_INVERTER_TIME_READ, 0x4)
    if content is None:
        LOGGER.error("Failed to read inverter time")
        raise ServiceValidationError("Failed to read inverter time")
    [yyyy, mm, dd, hh, mi, ss, zz] = unpack_from(">HBBBBBB", content)  # zz = weekday
    inverter_time = datetime(yyyy, mm, dd, hh, mi, ss)
    LOGGER.debug(f"Current inverter time: {inverter_time.isoformat()}, weekday: {zz}")

    # Determine local time
    local_tz = ZoneInfo(call.hass.config.time_zone or "UTC")  # use system timezone
    local_time = datetime.now(local_tz).replace(microsecond=0)
    LOGGER.debug(
        f"Local time: {local_time.isoformat()}, weekday: {local_time.isoweekday()}"
    )

    # Write local time to inverter
    # We can ignore weekday (and send 00) as it's calculated by inverter
    year = local_time.year
    month_day = local_time.month << 8 | local_time.day
    hour_minute = local_time.hour << 8 | local_time.minute
    second_zz = local_time.second << 8  # zz = 00
    # second_weekday = local_time.second << 8 | local_time.isoweekday()
    await mqtt_client.write_registers(
        MODBUS_REG_INVERTER_TIME_WRITE,
        [year, month_day, hour_minute, second_zz],
    )
    LOGGER.info(f"Inverter time synchronized to local time: {local_time.isoformat()}")

    # Return response
    return {"time": local_time.isoformat()}


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up SAJ H1 MQTT services."""

    LOGGER.debug(f"Registering service: {SERVICE_READ_REGISTER}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_REGISTER,
        read_register,
        schema=vol.Schema(
            vol.All(
                {
                    vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector(),
                    vol.Required(ATTR_REGISTER): cv.string,
                    vol.Optional(ATTR_REGISTER_FORMAT, default=None): vol.Any(
                        cv.string, None
                    ),
                }
            )
        ),
        supports_response=SupportsResponse.ONLY,
    )

    LOGGER.debug(f"Registering service: {SERVICE_READ_REGISTERS}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_REGISTERS,
        read_registers,
        schema=vol.Schema(
            vol.All(
                {
                    vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector(),
                    vol.Required(ATTR_REGISTER): cv.string,
                    vol.Required(ATTR_REGISTER_SIZE): cv.string,
                    vol.Optional(ATTR_REGISTER_FORMAT, default=None): vol.Any(
                        cv.string, None
                    ),
                }
            )
        ),
        supports_response=SupportsResponse.ONLY,
    )

    LOGGER.debug(f"Registering service: {SERVICE_WRITE_REGISTER}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_WRITE_REGISTER,
        write_register,
        schema=vol.Schema(
            vol.All(
                {
                    vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector(),
                    vol.Required(ATTR_REGISTER): cv.string,
                    vol.Required(ATTR_REGISTER_VALUE): cv.string,
                }
            )
        ),
    )

    LOGGER.debug(f"Registering service: {SERVICE_REFRESH_INVERTER_DATA}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_INVERTER_DATA,
        refresh_inverter_data,
        schema=vol.Schema(
            vol.All({vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector()})
        ),
    )

    LOGGER.debug(f"Registering service: {SERVICE_REFRESH_BATTERY_DATA}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_BATTERY_DATA,
        refresh_battery_data,
        schema=vol.Schema(
            vol.All({vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector()})
        ),
    )

    LOGGER.debug(f"Registering service: {SERVICE_REFRESH_BATTERY_CONTROLLER_DATA}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_BATTERY_CONTROLLER_DATA,
        refresh_battery_controller_data,
        schema=vol.Schema(
            vol.All({vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector()})
        ),
    )

    LOGGER.debug(f"Registering service: {SERVICE_REFRESH_CONFIG_DATA}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_CONFIG_DATA,
        refresh_config_data,
        schema=vol.Schema(
            vol.All({vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector()})
        ),
    )

    LOGGER.debug(f"Registering service: {SERVICE_SYNC_INVERTER_TIME}")
    hass.services.async_register(
        DOMAIN,
        SERVICE_SYNC_INVERTER_TIME,
        sync_inverter_time,
        schema=vol.Schema(
            vol.All({vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector()})
        ),
        supports_response=SupportsResponse.ONLY,
    )


def _get_config_entry(
    hass: HomeAssistant, entry_id: str | None
) -> SajH1MqttConfigEntry:
    """Return the config entry or raise error if not found or not loaded."""
    # Get the specified config entry, or fallback to first one if not specified
    if not (entry := hass.config_entries.async_get_entry(entry_id)):
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries or len(entries) == 0:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_entry_not_found",
            )
        entry = entries[0]
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_loaded",
        )
    return entry
