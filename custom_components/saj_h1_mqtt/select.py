"""Select entities for the SAJ H1 MQTT integration."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER, MODBUS_REG_APP_MODE, AppMode
from .coordinator import SajH1MqttDataCoordinator
from .entity import SajH1MqttEntity, SajH1MqttEntityDescription
from .types import SajH1MqttConfigEntry


@dataclass(frozen=True, kw_only=True)
class SajH1MqttSelectEntityDescription(
    SelectEntityDescription, SajH1MqttEntityDescription
):
    """A class that describes SAJ H1 MQTT select entities."""

    modbus_register: int  # register for writing


APP_MODE_SELECT_DESCRIPTION = SajH1MqttSelectEntityDescription(
    key="app_mode",
    entity_category=EntityCategory.CONFIG,
    entity_registry_enabled_default=True,
    options=[x.name for x in AppMode],
    modbus_register_offset=0,
    modbus_register_data_type=">H",
    modbus_register_scale=None,
    value_fn=lambda x: AppMode(x).name,
    modbus_register=MODBUS_REG_APP_MODE,
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

    # Add app mode
    entity = SajH1MqttAppModeSelectEntity(
        coordinator_config_data, APP_MODE_SELECT_DESCRIPTION
    )
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
        self._register = description.modbus_register

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
        await self.coordinator.mqtt_client.write_register(self._register, app_mode)
        await self.coordinator.async_request_refresh()
