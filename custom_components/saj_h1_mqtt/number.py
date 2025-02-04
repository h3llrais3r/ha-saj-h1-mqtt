"""Select entities for the SAJ H1 MQTT integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    LOGGER,
    MODBUS_REG_BATTERY_SOC_BACKUP,
    MODBUS_REG_BATTERY_SOC_HIGH,
    MODBUS_REG_BATTERY_SOC_LOW,
    MODBUS_REG_GRID_CHARGE_POWER_LIMIT,
    MODBUS_REG_GRID_FEED_POWER_LIMIT,
)
from .coordinator import SajH1MqttDataCoordinator
from .entity import SajH1MqttEntity, SajH1MqttEntityConfig
from .types import SajH1MqttConfigEntry

# fmt: off

# Entity description format:
# (name, offset, data_type, scale, unit, device_class, state_class, enabled_default), (min_value, max_value, step, modbus_register)
GRID_CHARGE_POWER_LIMIT =("grid_charge_power_limit", 2, ">H", None, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, False), (100, 5000, 100, MODBUS_REG_GRID_CHARGE_POWER_LIMIT)
GRID_FEED_POWER_LIMIT=("grid_feed_power_limit", 4, ">H", None, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, False), (100, 5000, 100, MODBUS_REG_GRID_FEED_POWER_LIMIT)
BATTERY_SOC_BACKUP = ("battery_soc_backup", 84, ">H", None, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, True), (10, 100, 1, MODBUS_REG_BATTERY_SOC_BACKUP)
BATTERY_SOC_HIGH = ("battery_soc_high", 88, ">H", None, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, True), (50, 100, 1, MODBUS_REG_BATTERY_SOC_HIGH)
BATTERY_SOC_LOW = ("battery_soc_low", 90, ">H", None, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, True), (10, 50, 1, MODBUS_REG_BATTERY_SOC_LOW)

# fmt: on


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SajH1MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number entities based on a config entry."""
    # Only set up number entities when config data coordinator is enabled
    coordinator_config_data = entry.runtime_data.coordinator_config_data
    if not coordinator_config_data:
        return

    entities: list[SajH1MqttEntity] = []

    # Add grid charge power limit
    entity_config = SajH1MqttNumberEntityConfig(
        GRID_CHARGE_POWER_LIMIT[0], GRID_CHARGE_POWER_LIMIT[1]
    )
    entity = SajH1MqttNumberEntity(coordinator_config_data, entity_config)
    entities.append(entity)

    # Add grid feed power limit
    entity_config = SajH1MqttNumberEntityConfig(
        GRID_FEED_POWER_LIMIT[0], GRID_FEED_POWER_LIMIT[1]
    )
    entity = SajH1MqttNumberEntity(coordinator_config_data, entity_config)
    entities.append(entity)

    # Add battery soc backup
    entity_config = SajH1MqttNumberEntityConfig(
        BATTERY_SOC_BACKUP[0], BATTERY_SOC_BACKUP[1]
    )
    entity = SajH1MqttNumberEntity(coordinator_config_data, entity_config)
    entities.append(entity)

    # Add battery soc high
    entity_config = SajH1MqttNumberEntityConfig(
        BATTERY_SOC_HIGH[0], BATTERY_SOC_HIGH[1]
    )
    entity = SajH1MqttNumberEntity(coordinator_config_data, entity_config)
    entities.append(entity)

    # Add battery soc low
    entity_config = SajH1MqttNumberEntityConfig(BATTERY_SOC_LOW[0], BATTERY_SOC_LOW[1])
    entity = SajH1MqttNumberEntity(coordinator_config_data, entity_config)
    entities.append(entity)

    # Add the entities
    LOGGER.info(f"Setting up {len(entities)} number entities")
    async_add_entities(entities)


class SajH1MqttNumberEntityConfig(SajH1MqttEntityConfig):
    """SAJ H1 MQTT number entity configuration."""

    def __init__(self, config_tuple, extra_config_tuple) -> None:
        """Initialize the number entity configuration."""
        super().__init__(config_tuple)
        (min_value, max_value, step, modbus_register) = extra_config_tuple
        # Assign fields from extra config tuple
        self.min_value: float = min_value
        self.max_value: float = max_value
        self.step: float = step
        self.modbus_register: int = modbus_register


class SajH1MqttNumberEntity(SajH1MqttEntity, NumberEntity):
    """SAJ H1 MQTT number entity."""

    def __init__(
        self,
        coordinator: SajH1MqttDataCoordinator,
        entity_config: SajH1MqttNumberEntityConfig,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entity_config)
        # Set extra entity attributes
        self._attr_native_min_value = entity_config.min_value
        self.native_max_value = entity_config.max_value
        self.native_step = entity_config.step
        self.modbus_register = entity_config.modbus_register

    @property
    def _entity_type(self) -> str:
        return "number"

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return self._get_native_value()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            register_value = int(value)  # modbus register value must be int
        except ValueError as err:
            raise ValueError(f"Invalid value: {value}") from err

        # Write register and refresh coordinator
        await self.coordinator.mqtt_client.write_register(
            self.modbus_register, register_value
        )
        await self.coordinator.async_request_refresh()
