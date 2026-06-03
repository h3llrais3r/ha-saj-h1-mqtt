"""The SAJ H1 MQTT integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components import mqtt
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .client import SajH1Client, SajH1ModbusClient, SajH1MqttClient
from .const import (
    CONF_ENABLE_MODBUS_DEBUG,
    CONF_ENABLE_MQTT_DEBUG,
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
    DOMAIN,
    LOGGER,
    MQTT_READY,
    PROTOCOL_MODBUS,
    PROTOCOL_MQTT,
)
from .coordinator import (
    SajH1MqttBatteryControllerDataCoordinator,
    SajH1MqttBatteryDataCoordinator,
    SajH1MqttConfigDataCoordinator,
    SajH1MqttData,
    SajH1MqttInverterDataCoordinator,
    SajH1MqttRealtimeDataCoordinator,
)
from .services import async_setup_services
from .types import SajH1MqttConfigEntry

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up SAJ H1 MQTT integration."""
    # Setup services
    async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> bool:
    """Set up a config entry."""
    # Make sure MQTT integration is enabled and the client is available
    if not await mqtt.async_wait_for_mqtt_client(hass):
        LOGGER.error("MQTT integration is not available")
        raise ConfigEntryNotReady("MQTT integration not available")

    # Create hass data for our domain (to keep track of some data)
    if DOMAIN not in hass.data:
        # When hass is not yet running (startup), we consider mqtt not ready (no birth message yet)
        # When hass is already running (reload entry), we consider mqtt ready (birth message received in the past)
        mqtt_ready = hass.is_running
        hass.data.setdefault(DOMAIN, {MQTT_READY: mqtt_ready})

    # Get config data
    serial_number: str = entry.data[CONF_SERIAL_NUMBER]
    protocol: str = entry.options[CONF_PROTOCOL]
    scan_interval_realtime_data = timedelta(
        seconds=entry.options[CONF_SCAN_INTERVAL_REALTIME_DATA]
    )
    # Get protocol config data
    modbus_host: str = entry.options.get(CONF_MODBUS_HOST, None)
    modbus_port: int = entry.options.get(CONF_MODBUS_PORT, DEFAULT_MODBUS_PORT)
    modbus_debug: bool = entry.options.get(CONF_ENABLE_MODBUS_DEBUG, False)
    mqtt_debug: bool = entry.options.get(CONF_ENABLE_MQTT_DEBUG, False)
    # Get optional data
    interval = entry.options.get(CONF_SCAN_INTERVAL_INVERTER_DATA, None)
    scan_interval_inverter_data = timedelta(seconds=interval) if interval else None
    interval = entry.options.get(CONF_SCAN_INTERVAL_BATTERY_DATA, None)
    scan_interval_battery_data = timedelta(seconds=interval) if interval else None
    interval = entry.options.get(CONF_SCAN_INTERVAL_BATTERY_CONTROLLER_DATA, None)
    scan_interval_battery_controller_data = (
        timedelta(seconds=interval) if interval else None
    )
    interval = entry.options.get(CONF_SCAN_INTERVAL_CONFIG_DATA, None)
    scan_interval_config_data = timedelta(seconds=interval) if interval else None

    LOGGER.info(f"Setting up SAJ H1 inverter with serial: {serial_number}")
    LOGGER.info(f"Using protocol: {protocol}")
    LOGGER.info(f"Scan interval realtime data: {scan_interval_realtime_data}")
    LOGGER.info(
        f"Scan interval inverter data: {scan_interval_inverter_data or 'disabled'}"
    )
    LOGGER.info(
        f"Scan interval battery data: {scan_interval_battery_data or 'disabled'}"
    )
    LOGGER.info(
        f"Scan interval controller data: {scan_interval_battery_controller_data or 'disabled'}"
    )
    LOGGER.info(f"Scan interval config data: {scan_interval_config_data or 'disabled'}")

    # Setup client (default to mqtt)
    client: SajH1Client
    if protocol == PROTOCOL_MODBUS:
        client = SajH1ModbusClient(hass, modbus_host, modbus_port, modbus_debug)
    else:
        client = SajH1MqttClient(hass, serial_number, mqtt_debug)
    await client.connect()

    # Setup coordinators
    LOGGER.debug("Setting up coordinators")

    # Realtime data coordinator
    coordinator_realtime_data = SajH1MqttRealtimeDataCoordinator(
        hass, entry, client, scan_interval_realtime_data, "realtime_data"
    )

    # Inverter data coordinators
    coordinator_inverter_data: SajH1MqttInverterDataCoordinator | None = None
    if scan_interval_inverter_data:
        coordinator_inverter_data = SajH1MqttInverterDataCoordinator(
            hass, entry, client, scan_interval_inverter_data, "inverter_data"
        )

    # Battery data coordinator
    coordinator_battery_data: SajH1MqttBatteryDataCoordinator | None = None
    if scan_interval_battery_data:
        coordinator_battery_data = SajH1MqttBatteryDataCoordinator(
            hass, entry, client, scan_interval_battery_data, "battery_data"
        )

    # Battery controller data coordinators
    coordinator_battery_controller_data: (
        SajH1MqttBatteryControllerDataCoordinator | None
    ) = None
    if scan_interval_battery_controller_data:
        coordinator_battery_controller_data = SajH1MqttBatteryControllerDataCoordinator(
            hass,
            entry,
            client,
            scan_interval_battery_controller_data,
            "battery_controller_data",
        )

    # Config data coordinator
    coordinator_config_data: SajH1MqttConfigDataCoordinator | None = None
    if scan_interval_config_data:
        coordinator_config_data = SajH1MqttConfigDataCoordinator(
            hass, entry, client, scan_interval_config_data, "config_data"
        )

    # Entry runtime data
    entry.runtime_data = SajH1MqttData(
        client=client,
        coordinator_realtime_data=coordinator_realtime_data,
        coordinator_inverter_data=coordinator_inverter_data,
        coordinator_battery_data=coordinator_battery_data,
        coordinator_battery_controller_data=coordinator_battery_controller_data,
        coordinator_config_data=coordinator_config_data,
    )

    # Trigger first refresh
    # If protocol is modbus, refresh immediately
    # If mqtt ready (or birth message disabled), refresh immediately (case when you reload the integration)
    # If mqtt not ready, wait for mqtt birth message before refresh (case when starting up homeassistant)
    if (
        protocol == PROTOCOL_MODBUS
        or hass.data[DOMAIN][MQTT_READY]
        or not _get_birth_message_topic(hass)
    ):
        await entry.runtime_data.async_first_refresh()
    else:
        await async_first_refresh_on_mqtt_birth_message(hass, entry)

    LOGGER.debug(f"Setting up plaforms: {[p.value for p in PLATFORMS]}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when it is updated (options flow)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> bool:
    """Migrate old config entries."""

    if entry.version > 2:
        # This means the user has downgraded from a future version
        return False

    if entry.version == 1:
        # Update from version 1 to version 2 (set default protocol to mqtt)
        new_options = {**entry.options}
        new_options[CONF_PROTOCOL] = PROTOCOL_MQTT
        hass.config_entries.async_update_entry(entry, options=new_options, version=2)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> None:
    """Reload a config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Disconnect the client
        await entry.runtime_data.client.disconnect()

    return unload_ok


async def async_first_refresh_on_mqtt_birth_message(
    hass: HomeAssistant, entry: SajH1MqttConfigEntry
) -> None:
    """Wait for mqtt birth message before triggering initial refresh.

    Because mqtt discovery can delay the birth message,
    we need to wait until the birth message before triggering the initial refresh.
    """

    async def on_message(msg: mqtt.ReceiveMessage):
        LOGGER.debug(f"Received birth message: {msg.payload}")
        # Mark mqtt ready
        hass.data[DOMAIN][MQTT_READY] = True
        # Trigger initial refresh
        await entry.runtime_data.async_first_refresh()

        # Unsubscribe from the birth topic once we have processed it
        LOGGER.debug(f"Unsubscribing from birth topic: {topic}")
        unsubscribe_callback()

    # Subscribe to the birth message topic
    topic = _get_birth_message_topic(hass)
    if topic:
        LOGGER.debug(f"Subscribing to birth topic: {topic}")
        unsubscribe_callback = await mqtt.async_subscribe(hass, topic, on_message)


def _get_birth_message_topic(hass: HomeAssistant) -> str | None:
    try:
        mqtt_data: mqtt.MqttData = hass.data[mqtt.DOMAIN]
        return mqtt_data.client.conf[mqtt.CONF_BIRTH_MESSAGE][mqtt.CONF_TOPIC]
    except KeyError:
        LOGGER.warning(
            "No birth topic configured, triggering first refresh immediately (might cause timeout)"
        )
        return None
