"""Sensors for the SAJ H1 MQTT integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    LOGGER,
    AppMode,
    BatteryState,
    GridState,
    SolarState,
    SystemLoadState,
    WorkingMode,
)
from .entity import SajH1MqttEntity, SajH1MqttEntityConfig
from .types import SajH1MqttConfigEntry

# fmt: off

# Sensor description format:
# (name, offset, data_type, scale, unit, device_class, state_class, enabled_default)

# realtime data packet fields
MAP_SAJ_REALTIME_DATA = (
    # General info
    # ("year", 0x0, ">H", None, None, None, None, False),
    # ("month", 0x2, ">B", None, None, None, None, False),
    # ("day", 0x3, ">B", None, None, None, None, False),
    # ("hour", 0x4, ">B", None, None, None, None, False),
    # ("minute", 0x5, ">B", None, None, None, None, False),
    # ("second", 0x6, ">B", None, None, None, None, False),

    ("inverter_working_mode", 0x8, ">H", None, None, SensorDeviceClass.ENUM, WorkingMode, True),
    ("heatsink_temperature", 0x20, ">h", 0.1, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, True),
    ("earth_leakage_current", 0x24, ">H", 1.0, UnitOfElectricCurrent.MILLIAMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),

    # Grid data
    ("grid_voltage", 0x62, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("grid_current", 0x64, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("grid_frequency", 0x66, ">H", 0.01, UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, True),
    ("grid_dc_component", 0x68, ">h", 0.001, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("grid_power_active", 0x6a, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("grid_power_apparent", 0x6c, ">h", 1.0, UnitOfApparentPower.VOLT_AMPERE, SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT, True),
    ("grid_power_factor", 0x6e, ">h", 0.1, PERCENTAGE, SensorDeviceClass.POWER_FACTOR, SensorStateClass.MEASUREMENT, True),

    # Inverter data
    ("inverter_voltage", 0x8c, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("inverter_current", 0x8e, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("inverter_frequency", 0x90, ">H", 0.01, UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, True),
    ("inverter_power_active", 0x92, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("inverter_power_apparent", 0x94, ">h", 1.0, UnitOfApparentPower.VOLT_AMPERE, SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT, True),
    ("inverter_bus_master_voltage", 0xce, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("inverter_bus_slave_voltage", 0xd0, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),

    # Output data
    ("output_voltage", 0xaa, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("output_current", 0xac, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("output_frequency", 0xae, ">H", 0.01, UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, True),
    ("output_dc_voltage", 0xb0, ">h", 0.001, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("output_power_active", 0xb2, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("output_power_apparent", 0xb4, ">h", 1.0, UnitOfApparentPower.VOLT_AMPERE, SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT, True),

    # Battery data
    ("battery_voltage", 0xd2, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("battery_current", 0xd4, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("battery_control_current_1", 0xd6, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("battery_control_current_2", 0xd8, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("battery_power", 0xda, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("battery_temperature", 0xdc, ">h", 0.1, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, True),
    ("battery_soc", 0xde, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, True),

    # Photovoltaic data
    ("panel_array_1_voltage", 0xe2, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("panel_array_1_current", 0xe4, ">H", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("panel_array_1_power", 0xe6, ">H", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("panel_array_2_voltage", 0xe8, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, True),
    ("panel_array_2_current", 0xea, ">H", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, True),
    ("panel_array_2_power", 0xec, ">H", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),

    # Power summaries
    ("summary_system_load_power", 0x140, ">H", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_smart_meter_load_power_1", 0x142, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_photovoltaic_power", 0x14a, ">H", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_battery_power", 0x14c, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_grid_power", 0x14e, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_inverter_power", 0x152, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_backup_load_power", 0x156, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True),
    ("summary_smart_meter_load_power_2", 0x15a, ">h", 1.0, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, True)
)

# realtime data energy statistics packet fields
MAP_SAJ_REALTIME_DATA_ENERGY_STATS = (
    ('energy_photovoltaic', 0x17e, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True),
    ('energy_battery_charged', 0x18e, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True),
    ('energy_battery_discharged', 0x19e, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True),
    ('energy_system_load', 0x1be, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True),
    ('energy_backup_load', 0x1ce, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True),
    ('energy_grid_exported', 0x1de, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True),
    ('energy_grid_imported', 0x1ee, ">I", 0.01, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, True)
)

# inverter data packet fields
MAP_SAJ_INVERTER_DATA = (
    ("inverter_type", 0, ">H", None, None, None, None, False),
    ("inverter_sub_type", 2, ">H", None, None, None, None, False),
    ("inverter_comm_pro_version", 4, ">H", 0.001, None, None, None, False),
    ("inverter_serial_number", 6, ">S20", None, None, None, None, True),
    ("inverter_product_code", 26, ">S20", None, None, None, None, False),
    ("inverter_display_sw_version", 46, ">H", "0.001", None, None, None, True),
    ("inverter_master_control_sw_version", 48, ">H", "0.001", None, None, None, True),
    ("inverter_slave_control_sw_version", 50, ">H", "0.001", None, None, None, False),
    ("inverter_display_board_hw_version", 52, ">H", "0.001", None, None, None, False),
    ("inverter_control_board_hw_version", 54, ">H", "0.001", None, None, None, False),
    ("inverter_power_board_hw_version", 56, ">H", "0.001", None, None, None, False),
    ("inverter_battery_numbers", 58, ">H", None, None, None, None, False), # always 0
)

# battery data packet fields
MAP_SAJ_BATTERY_DATA = (
    ("battery_1_bms_type", 0, ">H", None, None, None, None, False),
    ("battery_1_bms_serial_number", 2, ">S16", None, None, None, None, False),
    ("battery_1_bms_sw_version", 18, ">H", "0.001", None, None, None, False),
    ("battery_1_bms_hw_version", 20, ">H", "0.001", None, None, None, False),
    ("battery_1_type", 22, ">H", None, None, None, None, False),
    ("battery_1_serial_number", 24, ">S16", None, None, None, None, False),
    ("battery_2_bms_type", 40, ">H", None, None, None, None, False),
    ("battery_2_bms_serial_number", 42, ">S16", None, None, None, None, False),
    ("battery_2_bms_sw_version", 58, ">H", "0.001", None, None, None, False),
    ("battery_2_bms_hw_version", 60, ">H", "0.001", None, None, None, False),
    ("battery_2_type", 62, ">H", None, None, None, None, False),
    ("battery_2_serial_number", 64, ">S16", None, None, None, None, False),
    ("battery_3_bms_type", 80, ">H", None, None, None, None, False),
    ("battery_3_bms_serial_number", 82, ">S16", None, None, None, None, False),
    ("battery_3_bms_sw_version", 98, ">H", "0.001", None, None, None, False),
    ("battery_3_bms_hw_version", 100, ">H", "0.001", None, None, None, False),
    ("battery_3_type", 102, ">H", None, None, None, None, False),
    ("battery_3_serial_number", 104, ">S16", None, None, None, None, False),
    ("battery_4_bms_type", 120, ">H", None, None, None, None, False),
    ("battery_4_bms_serial_number", 122, ">S16", None, None, None, None, False),
    ("battery_4_bms_sw_version", 138, ">H", "0.001", None, None, None, False),
    ("battery_4_bms_hw_version", 140, ">H", "0.001", None, None, None, False),
    ("battery_4_type", 142, ">H", None, None, None, None, False),
    ("battery_4_serial_number", 144, ">S16", None, None, None, None, False),
)

# battery controller data packet fields
MAP_SAJ_BATTERY_CONTROLLER_DATA = (
    ("battery_numbers", 0, ">H", None, None, None, None, True),
    ("battery_capacity", 2, ">H", None, "AH", None, None, False),
    ("battery_1_fault", 4, ">H", None, None, None, None, False),
    ("battery_1_warning", 6, ">H", None, None, None, None, False),
    ("battery_2_fault", 8, ">H", None, None, None, None, False),
    ("battery_2_warning", 10, ">H", None, None, None, None, False),
    ("battery_3_fault", 12, ">H", None, None, None, None, False),
    ("battery_3_warning", 14, ">H", None, None, None, None, False),
    ("battery_4_fault", 16, ">H", None, None, None, None, False),
    ("battery_4_warning", 18, ">H", None, None, None, None, False),
    #("controller_reserve", 20, ">HH", None, None, None, None, False),
    ("battery_1_soc", 24, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_1_soh", 26, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_1_voltage", 28, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, False),
    ("battery_1_current", 30, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, False),
    ("battery_1_temperature", 32, ">h", 0.1, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, False),
    ("battery_1_cycle_num", 34, ">H", None, None, None, None, False),
    ("battery_2_soc", 36, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_2_soh", 38, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_2_voltage", 40, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, False),
    ("battery_2_current", 42, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, False),
    ("battery_2_temperature", 44, ">h", 0.1, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, False),
    ("battery_2_cycle_num", 46, ">H", None, None, None, None, False),
    ("battery_3_soc", 48, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_3_soh", 50, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_3_voltage", 52, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, False),
    ("battery_3_current", 54, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, False),
    ("battery_3_temperature", 56, ">h", 0.1, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, False),
    ("battery_3_cycle_num", 58, ">H", None, None, None, None, False),
    ("battery_4_soc", 60, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_4_soh", 62, ">H", 0.01, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_4_voltage", 64, ">H", 0.1, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, False),
    ("battery_4_current", 66, ">h", 0.01, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, False),
    ("battery_4_temperature", 68, ">h", 0.1, UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, False),
    ("battery_4_cycle_num", 70, ">H", None, None, None, None, False),
)

# config data packet fields
MAP_SAJ_CONFIG_DATA = (
    ("app_mode", 0, ">H", None, None, SensorDeviceClass.ENUM, AppMode, True),
    ("grid_charge_power_limit", 2, ">H", None, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, False),
    ("grid_feed_power_limit", 4, ">H", None, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, False),
    # unwanted data
    ("battery_soc_high", 88, ">H", None, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
    ("battery_soc_low", 90, ">H", None, PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, False),
)

# Custom sensors (based on realtime data)
SOLAR_STATE_SENSOR = ("solar_state", 0x14a, ">H", 1.0, None, None, None, True)
BATTERY_STATE_SENSOR = ("battery_state", 0x14c, ">h", 1.0, None, None, None, True)
GRID_STATE_SENSOR = ("grid_state", 0x15a, ">h", 1.0, None, None, None, True)
SYSTEM_LOAD_SENSOR = ("system_load_state", 0x140, ">H", 1.0, None, None, None, True)

# fmt: on


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SajH1MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities based on a config entry."""
    entities: list[SajH1MqttSensorEntity] = []

    # Get coordinators (only realtime data is required, all others are optional)
    coordinator_realtime_data = entry.runtime_data.coordinator_realtime_data
    coordinator_inverter_data = entry.runtime_data.coordinator_inverter_data
    coordinator_battery_data = entry.runtime_data.coordinator_battery_controller_data
    coordinator_battery_controller_data = (
        entry.runtime_data.coordinator_battery_controller_data
    )
    coordinator_config_data = entry.runtime_data.coordinator_config_data

    # Realtime data sensors
    for config_tuple in MAP_SAJ_REALTIME_DATA:
        entity_config = SajH1MqttSensorEntityConfig(config_tuple)
        entity = SajH1MqttSensorEntity(coordinator_realtime_data, entity_config)
        entities.append(entity)

    # Realtime data energy statistics sensors
    for config_tuple in MAP_SAJ_REALTIME_DATA_ENERGY_STATS:
        (
            name,
            offset,
            data_type,
            scale,
            unit,
            device_class,
            state_class,
            enabled_default,
        ) = config_tuple
        # 4 statistics for each type
        for period in "daily", "monthly", "yearly", "total":
            # Create new stats sensor tuple with new name
            sensor_name = f"{name}_{period}"
            stats_sensor_tuple = (
                sensor_name,
                offset,
                data_type,
                scale,
                unit,
                device_class,
                state_class,
                enabled_default,
            )
            entity_config = SajH1MqttSensorEntityConfig(stats_sensor_tuple)
            entity = SajH1MqttSensorEntity(coordinator_realtime_data, entity_config)
            entities.append(entity)
            # Update offset for next period
            offset += 4

    # Inverter sensors
    if coordinator_inverter_data:
        for config_tuple in MAP_SAJ_INVERTER_DATA:
            entity_config = SajH1MqttSensorEntityConfig(config_tuple)
            entity = SajH1MqttSensorEntity(coordinator_inverter_data, entity_config)
            entities.append(entity)

    # Battery sensors
    if coordinator_battery_data:
        for config_tuple in MAP_SAJ_BATTERY_DATA:
            entity_config = SajH1MqttSensorEntityConfig(config_tuple)
            entity = SajH1MqttSensorEntity(coordinator_battery_data, entity_config)
            entities.append(entity)

    # Battery controller sensors
    if coordinator_battery_controller_data:
        for config_tuple in MAP_SAJ_BATTERY_CONTROLLER_DATA:
            entity_config = SajH1MqttSensorEntityConfig(config_tuple)
            entity = SajH1MqttSensorEntity(
                coordinator_battery_controller_data, entity_config
            )
            entities.append(entity)

    # Config sensors
    if coordinator_config_data:
        for config_tuple in MAP_SAJ_CONFIG_DATA:
            entity_config = SajH1MqttSensorEntityConfig(config_tuple)
            entity = SajH1MqttSensorEntity(coordinator_config_data, entity_config)
            entities.append(entity)

    # Custom realtime data sensors

    # Solar state sensor
    entity_config = SajH1MqttSensorEntityConfig(SOLAR_STATE_SENSOR)
    entity = SajH1MqttSolarStateSensorEntity(coordinator_realtime_data, entity_config)
    entities.append(entity)

    # Battery state sensor
    entity_config = SajH1MqttSensorEntityConfig(BATTERY_STATE_SENSOR)
    entity = SajH1MqttBatteryStateSensorEntity(coordinator_realtime_data, entity_config)
    entities.append(entity)

    # Grid state sensor
    entity_config = SajH1MqttSensorEntityConfig(GRID_STATE_SENSOR)
    entity = SajH1MqttGridStateSensorEntity(coordinator_realtime_data, entity_config)
    entities.append(entity)

    # System load sensor
    entity_config = SajH1MqttSensorEntityConfig(SYSTEM_LOAD_SENSOR)
    entity = SajH1MqttSystemLoadStateSensorEntity(
        coordinator_realtime_data, entity_config
    )
    entities.append(entity)

    # Add the entities
    LOGGER.info(f"Setting up {len(entities)} sensor entities")
    async_add_entities(entities)


class SajH1MqttSensorEntityConfig(SajH1MqttEntityConfig):
    """SAJ H1 MQTT sensor entity configuration."""


class SajH1MqttSensorEntity(SajH1MqttEntity, SensorEntity):
    """SAJ H1 MQTT sensor entity."""

    @property
    def _entity_type(self) -> str:
        return "sensor"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the native value to represent the entity state."""
        return self._get_native_value()


class SajH1MqttSolarStateSensorEntity(SajH1MqttSensorEntity):
    """SAJ H1 MQTT solar state sensor entity."""

    @property
    def native_value(self) -> str | None:
        """Return the native value to represent the entity state."""
        val = self._get_native_value()
        if val is None:
            return None
        if val > 0:
            return SolarState.PRODUCING.value
        return SolarState.STANDBY.value


class SajH1MqttBatteryStateSensorEntity(SajH1MqttSensorEntity):
    """SAJ H1 MQTT battery state sensor entity."""

    @property
    def native_value(self) -> str | None:
        """Return the native value to represent the entity state."""
        val = self._get_native_value()
        if val is None:
            return None
        if val < 0:
            return BatteryState.CHARGING.value
        if val > 0:
            return BatteryState.DISCHARGING.value
        return BatteryState.STANDBY.value


class SajH1MqttGridStateSensorEntity(SajH1MqttSensorEntity):
    """SAJ H1 MQTT grid state sensor entity."""

    @property
    def native_value(self) -> str | None:
        """Return the native value to represent the entity state."""
        val = self._get_native_value()
        if val is None:
            return None
        if val < 0:
            return GridState.IMPORTING.value
        if val > 0:
            return GridState.EXPORTING.value
        return GridState.STANDBY.value


class SajH1MqttSystemLoadStateSensorEntity(SajH1MqttSensorEntity):
    """SAJ H1 MQTT system load state sensor entity."""

    @property
    def native_value(self) -> str | None:
        """Return the native value to represent the entity state."""
        val = self._get_native_value()
        if val is None:
            return None
        if val > 0:
            return SystemLoadState.CONSUMING.value
        return SystemLoadState.STANDBY.value
