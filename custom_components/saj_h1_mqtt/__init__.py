"""The SAJ H1 MQTT integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components import mqtt
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .client import SajH1MqttClient
from .const import (
    CONF_ENABLE_MQTT_DEBUG,
    CONF_SCAN_INTERVAL_BATTERY_CONTROLLER_DATA,
    CONF_SCAN_INTERVAL_BATTERY_DATA,
    CONF_SCAN_INTERVAL_CONFIG_DATA,
    CONF_SCAN_INTERVAL_INVERTER_DATA,
    CONF_SCAN_INTERVAL_REALTIME_DATA,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    LOGGER,
    MQTT_READY,
)
from .coordinator import (
    SajH1MqttBatteryControllerDataCoordinator,
    SajH1MqttBatteryDataCoordinator,
    SajH1MqttConfigDataCoordinator,
    SajH1MqttData,
    SajH1MqttInverterDataCoordinator,
    SajH1MqttRealtimeDataCoordinator,
)
from .services import async_register_services, async_remove_services
from .types import SajH1MqttConfigEntry

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> bool:
    """Set up a config entry."""
    # Make sure MQTT integration is enabled and the client is available
    if not await mqtt.async_wait_for_mqtt_client(hass):
        LOGGER.error("MQTT integration is not available")
        raise ConfigEntryNotReady("MQTT integration not available")

    # Create hass data for our domain (to keep track of some data)
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {MQTT_READY: False})

    # Get config data
    serial_number: str = entry.data[CONF_SERIAL_NUMBER]
    scan_interval_realtime_data = timedelta(
        seconds=entry.options[CONF_SCAN_INTERVAL_REALTIME_DATA]
    )
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
    debug_mqtt: bool = entry.options.get(CONF_ENABLE_MQTT_DEBUG, False)

    LOGGER.info(f"Setting up SAJ H1 inverter with serial: {serial_number}")
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

    # Setup mqtt client
    mqtt_client = SajH1MqttClient(hass, serial_number, debug_mqtt)
    await mqtt_client.connect()

    # Setup coordinators
    LOGGER.debug("Setting up coordinators")

    # Realtime data coordinator
    coordinator_realtime_data = SajH1MqttRealtimeDataCoordinator(
        hass, mqtt_client, scan_interval_realtime_data, "realtime_data"
    )

    # Inverter data coordinators
    coordinator_inverter_data: SajH1MqttInverterDataCoordinator | None = None
    if scan_interval_inverter_data:
        coordinator_inverter_data = SajH1MqttInverterDataCoordinator(
            hass, mqtt_client, scan_interval_inverter_data, "inverter_data"
        )

    # Battery data coordinator
    coordinator_battery_data: SajH1MqttBatteryDataCoordinator | None = None
    if scan_interval_battery_data:
        coordinator_battery_data = SajH1MqttBatteryDataCoordinator(
            hass, mqtt_client, scan_interval_battery_data, "battery_data"
        )

    # Battery controller data coordinators
    coordinator_battery_controller_data: (
        SajH1MqttBatteryControllerDataCoordinator | None
    ) = None
    if scan_interval_battery_controller_data:
        coordinator_battery_controller_data = SajH1MqttBatteryControllerDataCoordinator(
            hass,
            mqtt_client,
            scan_interval_battery_controller_data,
            "battery_controller_data",
        )

    # Config data coordinator
    coordinator_config_data: SajH1MqttConfigDataCoordinator | None = None
    if scan_interval_config_data:
        coordinator_config_data = SajH1MqttConfigDataCoordinator(
            hass, mqtt_client, scan_interval_config_data, "config_data"
        )

    # Entry runtime data
    entry.runtime_data = SajH1MqttData(
        mqtt_client=mqtt_client,
        coordinator_realtime_data=coordinator_realtime_data,
        coordinator_inverter_data=coordinator_inverter_data,
        coordinator_battery_data=coordinator_battery_data,
        coordinator_battery_controller_data=coordinator_battery_controller_data,
        coordinator_config_data=coordinator_config_data,
    )

    # Trigger first refresh
    # If mqtt ready, refresh immediately (case when you reload the integration)
    # If mqtt not ready, wait for mqtt birth message before refresh (case when starting up homeassistant)
    if hass.data[DOMAIN][MQTT_READY]:
        await entry.runtime_data.async_first_refresh()
    else:
        await async_first_refresh_on_mqtt_birth_message(hass, entry)

    LOGGER.debug(f"Setting up plaforms: {[p.value for p in PLATFORMS]}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async_register_services(hass)

    # Reload entry when it is updated (options flow)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> None:
    """Reload a config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SajH1MqttConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Remove services and disconnect the mqtt client
        async_remove_services(hass)
        await entry.runtime_data.mqtt_client.disconnect()

    return unload_ok


async def async_first_refresh_on_mqtt_birth_message(
    hass: HomeAssistant, entry: SajH1MqttConfigEntry
):
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
    topic = hass.data[mqtt.DOMAIN].client.conf[mqtt.CONF_BIRTH_MESSAGE][mqtt.CONF_TOPIC]
    unsubscribe_callback = await mqtt.async_subscribe(hass, topic, on_message)
