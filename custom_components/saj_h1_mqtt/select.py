"""Select entities for the SAJ H1 MQTT integration."""

from __future__ import annotations

from abc import ABC

from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER, MODBUS_REG_APP_MODE, AppMode
from .entity import SajH1MqttEntity, SajH1MqttEntityConfig
from .types import SajH1MqttConfigEntry

# fmt: off

# Sensor description format:
# (name, offset, data_type, scale, unit, device_class, state_class, enabled_default)
APP_MODE = ("app_mode", 0, ">H", None, None, SensorDeviceClass.ENUM, AppMode, True)

# fmt: on


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SajH1MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select entities based on a config entry."""
    # Only set up select entities when config data coordinator is enabled
    coordinator_config_data = entry.runtime_data.coordinator_config_data
    if not coordinator_config_data:
        return

    entities: list[SajH1MqttEntity] = []

    # Add app mode
    entity_config = SajH1MqttSelectEntityConfig(APP_MODE)
    entity = SajH1MqttAppModeSelectEntity(coordinator_config_data, entity_config)
    entities.append(entity)

    # Add the entities
    LOGGER.info(f"Setting up {len(entities)} select entities")
    async_add_entities(entities)


class SajH1MqttSelectEntityConfig(SajH1MqttEntityConfig):
    """SAJ H1 MQTT select entity configuration."""


class SajH1MqttSelectEntity(SajH1MqttEntity, SelectEntity, ABC):
    """SAJ H1 MQTT select entity.

    This is the base abstract class for all select entity classes.
    """

    @property
    def _entity_type(self) -> str:
        return "select"

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        value = self._get_native_value()
        return str(value) if value else None


class SajH1MqttAppModeSelectEntity(SajH1MqttSelectEntity):
    """SAJ H1 MQTT app mode select entity."""

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            app_mode = AppMode[option].value
        except KeyError as err:
            raise ValueError(f"Invalid option: {option}") from err

        # Write register and refresh coordinator
        await self.coordinator.mqtt_client.write_register(MODBUS_REG_APP_MODE, app_mode)
        await self.coordinator.async_request_refresh()
