"""Select entities for the SAJ H1 MQTT integration."""

from __future__ import annotations

from abc import ABC
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER, MODBUS_REG_APP_MODE, AppMode
from .coordinator import SajH1MqttDataCoordinator
from .entity import SajH1MqttEntity, SajH1MqttEntityDescription
from .types import SajH1MqttConfigEntry


async def _modbus_write_and_refresh_coordinator(
    coordinator: SajH1MqttDataCoordinator, modbus_register: int, modbus_value: int
) -> None:
    # Write modbus register and refresh coordinator
    await coordinator.mqtt_client.write_register(modbus_register, modbus_value)
    await coordinator.async_request_refresh()


@dataclass(frozen=True, kw_only=True)
class SajH1MqttSelectEntityDescription(
    SelectEntityDescription, SajH1MqttEntityDescription
):
    """A class that describes SAJ H1 MQTT select entities."""

    modbus_register: int
    modbus_value_fn: Callable[[int | float | str | None], int]


SELECT_ENTITY_DESCRIPTIONS: tuple[SajH1MqttSelectEntityDescription, ...] = (
    SajH1MqttSelectEntityDescription(
        key="app_mode",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        options=[x.name for x in AppMode],
        modbus_register_offset=0,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=lambda x: AppMode(x).name,
        modbus_register=MODBUS_REG_APP_MODE,
        modbus_value_fn=lambda x: AppMode[x].value,
    ),
)


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

    # Add all number entities
    for description in SELECT_ENTITY_DESCRIPTIONS:
        entity = SajH1MqttSelectEntity(coordinator_config_data, description)
        entities.append(entity)

    # Add the entities
    LOGGER.info(f"Setting up {len(entities)} select entities")
    async_add_entities(entities)


class SajH1MqttSelectEntity(SajH1MqttEntity, SelectEntity, ABC):
    """SAJ H1 MQTT select entity.

    This is the base abstract class for all select entity classes.
    """

    def __init__(
        self,
        coordinator: SajH1MqttDataCoordinator,
        description: SajH1MqttSelectEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description)
        # Custom fields from entity description
        self._modbus_register = description.modbus_register
        self._modbus_value_fn = description.modbus_value_fn

    @property
    def _entity_type(self) -> str:
        return "select"

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        value = self._get_native_value()
        return str(value) if value else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            modbus_value = self._modbus_value_fn(option)
        except Exception as err:
            raise ValueError(f"Invalid option: {option}") from err

        # Write modbus register and refresh coordinator
        await self.coordinator.mqtt_client.write_register(
            self._modbus_register, modbus_value
        )
        await self.coordinator.async_request_refresh()
