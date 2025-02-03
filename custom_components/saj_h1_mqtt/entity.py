"""Base entity for the SAJ H1 MQTT integration."""

from __future__ import annotations

from abc import abstractmethod
from struct import unpack_from
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BRAND,
    CONF_ENABLE_SERIAL_NUMBER_PREFIX,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
    MODEL,
    MODEL_SHORT,
)
from .coordinator import SajH1MqttDataCoordinator


class SajH1MqttEntityConfig:
    """SAJ H1 MQTT entity configuration."""

    def __init__(self, config_tuple) -> None:
        """Initialize the entity configuration."""
        (
            entity_name,
            offset,
            data_type,
            scale,
            unit,
            device_class,
            state_class,
            enabled_default,
        ) = config_tuple
        # Assign fields from config tuple
        self.entity_name: str = entity_name
        self.offset: int = offset
        self.data_type: str = data_type
        self.scale: float | str | None = scale
        self.unit: str | None = unit
        self.device_class: Any | None = device_class
        self.state_class: Any | None = state_class
        self.enabled_default: bool = enabled_default


class SajH1MqttEntity(CoordinatorEntity[SajH1MqttDataCoordinator], Entity):
    """SAJ H1 MQTT entity."""

    def __init__(
        self,
        coordinator: SajH1MqttDataCoordinator,
        entity_config: SajH1MqttEntityConfig,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        # Copy attributes from entity config
        self._entity_config = entity_config
        self._offset = entity_config.offset
        self._data_type = entity_config.data_type
        self._scale = entity_config.scale
        self._unit = entity_config.unit

        # Define entity prefixes
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

        # Set entity attributes (TODO: check if we need to suffix the unique_id with _{self._entity_type})
        self._attr_unique_id = (
            f"{self._unique_id_prefix}_{entity_config.entity_name}".lower()
        )
        self._attr_name = f"{self._name_prefix}_{entity_config.entity_name}".lower()
        self._attr_device_class = entity_config.device_class
        # Clear state class when device class is ENUM
        self._attr_state_class = (
            entity_config.state_class
            if entity_config.device_class is not SensorDeviceClass.ENUM
            else None
        )
        self._attr_native_unit_of_measurement = entity_config.unit
        # Use state class as enum class when device class is ENUM
        self.enum_class = (
            entity_config.state_class
            if entity_config.device_class is SensorDeviceClass.ENUM
            else None
        )
        # Set options as enum names when device class is ENUM
        self._attr_options = (
            [e.name for e in self.enum_class] if self.enum_class else None
        )
        self._attr_entity_registry_enabled_default = entity_config.enabled_default
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f"{BRAND} {self._serial_number}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=self._serial_number,
        )

        LOGGER.debug(f"Setting up entity: {self.name}")

    def _convert_native_value(
        self, value: float | str | None
    ) -> int | float | str | None:
        """Convert the native value.

        To be replaced by classes who want to have custom conversion logic.
        """
        return value

    def _get_native_value(self) -> int | float | str | None:
        """Get the native value for the entity."""
        # Return None if no coordinator data
        payload = self.coordinator.data
        if payload is None:
            return None

        # Get raw sensor value (>Sxx is custom type to indicate a string of length xx)
        value: int | float | str | None = None
        if self._data_type.startswith(">S"):
            reg_length = int(self._data_type.replace(">S", ""))
            value = bytearray.decode(payload[self._offset : self._offset + reg_length])
        else:
            (value,) = unpack_from(self._data_type, payload, self._offset)

        # Set sensor value (taking scale into account, scale should ALWAYS contain a .)
        if self._scale is not None:
            digits = max(0, str(self._scale)[::-1].find("."))
            value = round(value * float(self._scale), digits)
            # If scale is a str, format the value with the same precision
            if isinstance(self._scale, str):
                value = "{:.{precision}f}".format(value, precision=digits)

        # Convert enum sensor to the corresponding enum name
        if self.enum_class:
            value = self.enum_class(value).name

        # Custom conversion
        value = self._convert_native_value(value)

        LOGGER.debug(
            f"Entity: {self.entity_id}, value: {value}{' ' + self._unit if self._unit else ''}"
        )

        return value

    @property
    @abstractmethod
    def _entity_type(self) -> str:
        pass
