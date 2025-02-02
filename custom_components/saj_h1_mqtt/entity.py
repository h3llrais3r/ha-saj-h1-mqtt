"""Base entity for the SAJ H1 MQTT integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BRAND,
    CONF_ENABLE_SERIAL_NUMBER_PREFIX,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    MODEL_SHORT,
)
from .coordinator import SajH1MqttDataCoordinator


class SajH1MqttEntity(CoordinatorEntity[SajH1MqttDataCoordinator]):
    """SAJ H1 MQTT entity class."""

    def __init__(self, coordinator: SajH1MqttDataCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        # Set entity prefixes
        self._serial_number = coordinator.config_entry.data[CONF_SERIAL_NUMBER]
        self._use_serial_number_prefix = coordinator.config_entry.options[
            CONF_ENABLE_SERIAL_NUMBER_PREFIX
        ]
        self._unique_id_prefix = f"{BRAND}_{self._serial_number}"
        self._name_prefix = (
            f"{BRAND}_{self._serial_number}"
            if self._use_serial_number_prefix
            else f"{BRAND}_{MODEL_SHORT}"
        )

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f"{BRAND} {self._serial_number}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=self._serial_number,
        )
