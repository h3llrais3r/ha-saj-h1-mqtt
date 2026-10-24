"""Select entities for the SAJ H1 MQTT integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COORDINATOR_CONFIG_DATA,
    COORDINATOR_OPERATIONAL_CONFIG_DATA,
    LOGGER,
    MODBUS_REG_BATTERY_SOC_BACKUP,
    MODBUS_REG_BATTERY_SOC_HIGH,
    MODBUS_REG_BATTERY_SOC_LOW,
    MODBUS_REG_GRID_CHARGE_POWER_LIMIT,
    MODBUS_REG_GRID_FEED_POWER_LIMIT,
    MODBUS_REG_PASSIVE_GRID_CHARGE_POWER,
    MODBUS_REG_PASSIVE_GRID_DISCHARGE_POWER,
)
from .coordinator import SajH1MqttDataCoordinator
from .entity import SajH1MqttEntity, SajH1MqttEntityDescription
from .types import SajH1MqttConfigEntry


@dataclass(frozen=True, kw_only=True)
class SajH1MqttNumberEntityDescription(
    NumberEntityDescription, SajH1MqttEntityDescription
):
    """A class that describes SAJ H1 MQTT number entities."""

    modbus_register: int
    coordinator_name: str


NUMBER_ENTITY_DESCRIPTIONS: tuple[SajH1MqttNumberEntityDescription, ...] = (
    SajH1MqttNumberEntityDescription(
        key="grid_charge_power_limit",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=100,
        native_max_value=5000,
        native_step=100,
        modbus_register_offset=2,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_GRID_CHARGE_POWER_LIMIT,
        coordinator_name=COORDINATOR_CONFIG_DATA,
    ),
    SajH1MqttNumberEntityDescription(
        key="grid_feed_power_limit",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=100,
        native_max_value=5000,
        native_step=100,
        modbus_register_offset=4,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_GRID_FEED_POWER_LIMIT,
        coordinator_name=COORDINATOR_CONFIG_DATA,
    ),
    SajH1MqttNumberEntityDescription(
        key="battery_soc_backup",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        device_class=NumberDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        modbus_register_offset=84,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_BATTERY_SOC_BACKUP,
        coordinator_name=COORDINATOR_CONFIG_DATA,
    ),
    SajH1MqttNumberEntityDescription(
        key="battery_soc_high",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        device_class=NumberDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=50,
        native_max_value=100,
        native_step=1,
        modbus_register_offset=88,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_BATTERY_SOC_HIGH,
        coordinator_name=COORDINATOR_CONFIG_DATA,
    ),
    SajH1MqttNumberEntityDescription(
        key="battery_soc_low",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        device_class=NumberDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=10,
        native_max_value=50,
        native_step=1,
        modbus_register_offset=90,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_BATTERY_SOC_LOW,
        coordinator_name=COORDINATOR_CONFIG_DATA,
    ),
    SajH1MqttNumberEntityDescription(
        key="passive_grid_charge_power",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=5000,
        native_step=100,
        modbus_register_offset=102,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_PASSIVE_GRID_CHARGE_POWER,
        coordinator_name=COORDINATOR_OPERATIONAL_CONFIG_DATA,
    ),
    SajH1MqttNumberEntityDescription(
        key="passive_grid_discharge_power",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=5000,
        native_step=100,
        modbus_register_offset=104,
        modbus_register_data_type=">H",
        modbus_register_scale=None,
        value_fn=None,
        modbus_register=MODBUS_REG_PASSIVE_GRID_DISCHARGE_POWER,
        coordinator_name=COORDINATOR_OPERATIONAL_CONFIG_DATA,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SajH1MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number entities based on a config entry."""
    # Only set up number entities when config data coordinators are enabled
    coordinator_config_data = entry.runtime_data.coordinator_config_data
    coordinator_operational_config_data = (
        entry.runtime_data.coordinator_operational_config_data
    )
    if not coordinator_config_data and not coordinator_operational_config_data:
        return

    entities: list[SajH1MqttEntity] = []

    # Add all number entities
    for description in NUMBER_ENTITY_DESCRIPTIONS:
        if description.coordinator_name == COORDINATOR_CONFIG_DATA:
            entity = SajH1MqttNumberEntity(coordinator_config_data, description)
        elif description.coordinator_name == COORDINATOR_OPERATIONAL_CONFIG_DATA:
            entity = SajH1MqttNumberEntity(
                coordinator_operational_config_data, description
            )
        else:
            LOGGER.error(
                f"Unknown coordinator name {description.coordinator_name} for number entity {description.key}"
            )
            continue
        entities.append(entity)

    # Add the entities
    LOGGER.info(f"Setting up {len(entities)} number entities")
    async_add_entities(entities)


class SajH1MqttNumberEntity(SajH1MqttEntity, NumberEntity):
    """SAJ H1 MQTT number entity."""

    def __init__(
        self,
        coordinator: SajH1MqttDataCoordinator,
        description: SajH1MqttNumberEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description)

        # Custom fields from entity description
        self._modbus_register = description.modbus_register

    @property
    def _entity_type(self) -> str:
        return "number"

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        value = self._get_native_value()
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            modbus_value = int(value)  # modbus register value must be int
        except Exception as err:
            raise ValueError(f"Invalid value: {value}") from err

        # Write register and refresh coordinator
        await self.coordinator.client.write_register(
            self._modbus_register, modbus_value
        )
        await self.coordinator.async_request_refresh()
