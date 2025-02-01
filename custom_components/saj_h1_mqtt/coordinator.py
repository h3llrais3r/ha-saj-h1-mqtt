"""Coordinators for the SAJ H1 MQTT integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import SajH1MqttClient
from .const import DOMAIN, LOGGER
from .utils import log_hex


@dataclass
class SajH1MqttData:
    """SAJ H1 MQTT data."""

    mqtt_client: SajH1MqttClient
    coordinator_realtime_data: SajH1MqttRealtimeDataCoordinator
    coordinator_inverter_data: SajH1MqttInverterDataCoordinator | None
    coordinator_battery_data: SajH1MqttBatteryDataCoordinator | None
    coordinator_battery_controller_data: (
        SajH1MqttBatteryControllerDataCoordinator | None
    )
    coordinator_config_data: SajH1MqttConfigDataCoordinator | None


class SajH1MqttDataCoordinator(DataUpdateCoordinator):
    """SAJ H1 MQTT data coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        mqtt_client: SajH1MqttClient,
        scan_interval: timedelta,
    ) -> None:
        """Set up the SajH1MqttDataCoordinator class."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        self.mqtt_client = mqtt_client
        self.data: bytearray | None = None


class SajH1MqttRealtimeDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT realtime data coordinator."""

    async def _async_update_data(self) -> bytearray | None:
        """Fetch the realtime data."""
        reg_start = 0x4000
        reg_count = 0x100  # 256 registers
        LOGGER.debug(
            f"Fetching realtime data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttInverterDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT inverter data coordinator."""

    async def _async_update_data(self) -> bytearray | None:
        """Fetch the inverter info."""
        reg_start = 0x8F00
        reg_count = 0x1E  # 30 registers
        LOGGER.debug(
            f"Fetching inverter info at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttBatteryDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT battery data coordinator."""

    async def _async_update_data(self) -> bytearray | None:
        """Fetch the battery info."""
        reg_start = 0x8E00
        reg_count = 0x50  # 80 registers
        LOGGER.debug(
            f"Fetching battery info at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttBatteryControllerDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT battery controller data coordinator."""

    async def _async_update_data(self) -> bytearray | None:
        """Fetch the battery controller data."""
        reg_start = 0xA000
        reg_count = 0x24  # 36 registers
        LOGGER.debug(
            f"Fetching battery controller data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttConfigDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT config data coordinator."""

    async def _async_update_data(self) -> bytearray | None:
        """Fetch the config data."""
        reg_start = 0x3247
        reg_count = 0x2E  # 46 registers
        LOGGER.debug(
            f"Fetching config data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)
