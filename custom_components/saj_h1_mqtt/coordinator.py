"""Coordinators for the SAJ H1 MQTT integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
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

    def mark_coordinators_ready(self) -> None:
        """Mark all coordinators ready."""
        self.coordinator_realtime_data.ready = True
        if self.coordinator_inverter_data:
            self.coordinator_inverter_data.ready = True
        if self.coordinator_battery_data:
            self.coordinator_battery_data.ready = True
        if self.coordinator_battery_controller_data:
            self.coordinator_battery_controller_data.ready = True
        if self.coordinator_config_data:
            self.coordinator_config_data.ready = True

    async def async_refresh_coordinators(self) -> None:
        """Refresh all coordinators."""
        await self.coordinator_realtime_data.async_refresh()
        if self.coordinator_inverter_data:
            await self.coordinator_inverter_data.async_refresh()
        if self.coordinator_battery_data:
            await self.coordinator_battery_data.async_refresh()
        if self.coordinator_battery_controller_data:
            await self.coordinator_battery_controller_data.async_refresh()
        if self.coordinator_config_data:
            await self.coordinator_config_data.async_refresh()

    async def async_first_refresh(self) -> None:
        """Trigger first refresh for all coordinators."""
        LOGGER.debug("Triggering coordinator(s) first refresh")
        self.mark_coordinators_ready()
        await self.async_refresh_coordinators()


class SajH1MqttDataCoordinator(DataUpdateCoordinator, ABC):
    """SAJ H1 MQTT data coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        mqtt_client: SajH1MqttClient,
        scan_interval: timedelta,
        name: str,
    ) -> None:
        """Set up the SajH1MqttDataCoordinator class."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{name}_coordinator",
            update_interval=scan_interval,
        )
        self.mqtt_client = mqtt_client
        self.data: bytearray | None = None
        self.ready = False

    @abstractmethod
    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the latest data from the source."""
        raise NotImplementedError

    async def _async_update_data(self) -> bytearray | None:
        # If coordinator is not ready (due to mqtt discovery), skip the fetching of the data
        if not self.ready:
            LOGGER.debug(f"Skipping data fetching, {self.name} not ready yet")
            return None
        return await self._async_fetch_data()


class SajH1MqttRealtimeDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT realtime data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the realtime data."""
        reg_start = 0x4000
        reg_count = 0x100  # 256 registers
        LOGGER.debug(
            f"Fetching realtime data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttInverterDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT inverter data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the inverter data."""
        reg_start = 0x8F00
        reg_count = 0x1E  # 30 registers
        LOGGER.debug(
            f"Fetching inverter data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttBatteryDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT battery data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the battery bata."""
        reg_start = 0x8E00
        reg_count = 0x50  # 80 registers
        LOGGER.debug(
            f"Fetching battery data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttBatteryControllerDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT battery controller data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the battery controller data."""
        reg_start = 0xA000
        reg_count = 0x24  # 36 registers
        LOGGER.debug(
            f"Fetching battery controller data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajH1MqttConfigDataCoordinator(SajH1MqttDataCoordinator):
    """SAJ H1 MQTT config data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the config data."""
        reg_start = 0x3247
        reg_count = 0x2E  # 46 registers
        LOGGER.debug(
            f"Fetching config data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)
