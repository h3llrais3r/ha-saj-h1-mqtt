"""Sensors for the SAJ H1 MQTT integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
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
    CONF_ENABLE_ACCURATE_REALTIME_POWER_DATA,
    LOGGER,
    AppMode,
    BatteryState,
    GridState,
    PVState,
    SystemLoadState,
    WorkingMode,
)
from .coordinator import SajH1MqttDataCoordinator
from .entity import SajH1MqttEntity, SajH1MqttEntityDescription, get_entity_description
from .types import SajH1MqttConfigEntry


@dataclass(frozen=True, kw_only=True)
class SajH1MqttSensorEntityDescription(
    SensorEntityDescription, SajH1MqttEntityDescription
):
    """A class that describes SAJ H1 MQTT number entities."""


# fmt: off

# realtime data sensors
SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS: tuple[SajH1MqttSensorEntityDescription, ...] = (
    # Time data
    SajH1MqttSensorEntityDescription(key="time_year", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="time_month", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=2, modbus_register_data_type=">B", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="time_day", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=3, modbus_register_data_type=">B", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="time_hour", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=4, modbus_register_data_type=">B", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="time_minute", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=5, modbus_register_data_type=">B", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="time_second", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=6, modbus_register_data_type=">B", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="time_reserved", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=7, modbus_register_data_type=">B", modbus_register_scale=None, value_fn=None),

    # General data
    SajH1MqttSensorEntityDescription(key="inverter_working_mode", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x8, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: WorkingMode(x).name),
    SajH1MqttSensorEntityDescription(key="heatsink_temperature", entity_registry_enabled_default=True, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=0x20, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="earth_leakage_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, modbus_register_offset=0x24, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # Grid data
    SajH1MqttSensorEntityDescription(key="grid_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x62, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x64, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_frequency", entity_registry_enabled_default=True, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfFrequency.HERTZ, modbus_register_offset=0x66, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_dc_component", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x68, modbus_register_data_type=">h", modbus_register_scale=0.001, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_power_active", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x6a, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_power_apparent", entity_registry_enabled_default=True, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, modbus_register_offset=0x6c, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_power_factor", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0x6e, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),

    # Inverter data
    SajH1MqttSensorEntityDescription(key="inverter_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x8c, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x8e, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_frequency", entity_registry_enabled_default=True, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfFrequency.HERTZ, modbus_register_offset=0x90, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_power_active", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x92, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_power_apparent", entity_registry_enabled_default=True, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, modbus_register_offset=0x94, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_bus_master_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xce, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_bus_slave_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xd0, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),

    # Output data
    SajH1MqttSensorEntityDescription(key="output_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xaa, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="output_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0xac, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="output_frequency", entity_registry_enabled_default=True, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfFrequency.HERTZ, modbus_register_offset=0xae, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="output_dc_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xb0, modbus_register_data_type=">h", modbus_register_scale=0.001, value_fn=None),
    SajH1MqttSensorEntityDescription(key="output_power_active", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0xb2, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="output_power_apparent", entity_registry_enabled_default=True, device_class=SensorDeviceClass.APPARENT_POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE, modbus_register_offset=0xb4, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),

    # Battery data
    SajH1MqttSensorEntityDescription(key="battery_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xd2, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0xd4, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_control_current_1", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0xd6, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_control_current_2", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0xd8, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0xda, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_temperature", entity_registry_enabled_default=True, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=0xdc, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_soc", entity_registry_enabled_default=True, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0xde, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),

    # PV data
    SajH1MqttSensorEntityDescription(key="pv_array_1_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xe2, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="pv_array_1_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0xe4, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="pv_array_1_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0xe6, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="pv_array_2_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xe8, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="pv_array_2_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0xea, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="pv_array_2_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0xec, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # Power summaries
    SajH1MqttSensorEntityDescription(key="summary_system_load_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x140, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_smart_meter_load_power_1", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x142, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_pv_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x14a, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_battery_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x14c, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_grid_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x14e, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_inverter_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x152, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_backup_load_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x156, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajH1MqttSensorEntityDescription(key="summary_smart_meter_load_power_2", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x15a, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None)
)

# realtime data energy statistics sensors
SAJ_REALTIME_DATA_ENERGY_STATS_SENSOR_DESCRIPTIONS: tuple[SajH1MqttSensorEntityDescription, ...] = (
    SajH1MqttSensorEntityDescription(key="energy_pv", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x17e, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="energy_battery_charged", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x18e, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="energy_battery_discharged", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x19e, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="energy_system_load", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x1be, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="energy_backup_load", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x1ce, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="energy_grid_exported", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x1de, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="energy_grid_imported", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x1ee, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None)
)

# fmt: on

# Realtime power sensors (based on realtime data, to be used with power flow charts)
REALTIME_PV_POWER_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_pv_power",
    entity_registry_enabled_default=True,
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfPower.WATT,
    modbus_register_offset=0x14A,
    modbus_register_data_type=">H",
    modbus_register_scale=1.0,
    value_fn=None,
)
REALTIME_BATTERY_POWER_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_battery_power",
    entity_registry_enabled_default=True,
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfPower.WATT,
    modbus_register_offset=0x14C,
    modbus_register_data_type=">h",
    modbus_register_scale=1.0,
    value_fn=None,
)
REALTIME_GRID_POWER_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_grid_power",
    entity_registry_enabled_default=True,
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfPower.WATT,
    modbus_register_offset=0x15A,  # use summary_smart_meter_load_power_2 data
    modbus_register_data_type=">h",
    modbus_register_scale=-1.0,  # use inverted scale as value is inverted
    value_fn=None,
)
REALTIME_SYSTEM_LOAD_POWER_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_system_load_power",
    entity_registry_enabled_default=True,
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfPower.WATT,
    modbus_register_offset=0x140,
    modbus_register_data_type=">H",
    modbus_register_scale=1.0,
    value_fn=None,
)

# Realtime state sensors (based on realtime data)
REALTIME_PV_STATE_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_pv_state",
    entity_registry_enabled_default=True,
    device_class=None,
    state_class=None,
    native_unit_of_measurement=None,
    modbus_register_offset=0x14A,
    modbus_register_data_type=">H",
    modbus_register_scale=1.0,
    value_fn=lambda x: None
    if x is None
    else (PVState.PRODUCING.value if x > 0 else PVState.STANDBY.value),
)
REALTIME_BATTERY_STATE_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_battery_state",
    entity_registry_enabled_default=True,
    device_class=None,
    state_class=None,
    native_unit_of_measurement=None,
    modbus_register_offset=0x14C,
    modbus_register_data_type=">h",
    modbus_register_scale=1.0,
    value_fn=lambda x: None
    if x is None
    else (
        BatteryState.DISCHARGING.value
        if x > 0
        else (BatteryState.CHARGING.value if x < 0 else BatteryState.STANDBY.value)
    ),
)
REALTIME_GRID_STATE_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_grid_state",
    entity_registry_enabled_default=True,
    device_class=None,
    state_class=None,
    native_unit_of_measurement=None,
    modbus_register_offset=0x15A,  # use summary_smart_meter_load_power_2 data
    modbus_register_data_type=">h",
    modbus_register_scale=-1.0,  # use inverted scale as value is inverted
    value_fn=lambda x: None
    if x is None
    else (
        GridState.IMPORTING.value
        if x > 0
        else (GridState.EXPORTING.value if x < 0 else GridState.STANDBY.value)
    ),
)
REALTIME_SYSTEM_LOAD_STATE_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_system_load_state",
    entity_registry_enabled_default=True,
    device_class=None,
    state_class=None,
    native_unit_of_measurement=None,
    modbus_register_offset=0x140,
    modbus_register_data_type=">H",
    modbus_register_scale=1.0,
    value_fn=lambda x: None
    if x is None
    else (SystemLoadState.CONSUMING.value if x > 0 else GridState.STANDBY.value),
)

# Accurate realtime sensors (only used when enabled in config, replaces the original 'realtime_grid_power' and 'realtime_grid_state' sensors)
# SAJ did some update and is not showing the minimal import/export values from the grid anymore in their esolar app
# This means that the values of the 'realtime_system_load_power' are slightly adapted to hide those minor import/export values from the grid
# If we want to get the real accurate values back, we can use the readings from 'summary_smart_meter_load_power_1' sensor
# However, we need to recalculate the 'realtime_system_load_power' to make sure the balance is correct
# Formula: 'realtime_system_load_power' = 'summary_system_load_power' + 'summary_smart_meter_load_power_1' + 'summary_smart_meter_load_power_2' (which has inverted scale)
ACCURATE_REALTIME_GRID_POWER_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_grid_power",
    entity_registry_enabled_default=True,
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfPower.WATT,
    modbus_register_offset=0x142,  # use summary_smart_meter_load_power_1 data
    modbus_register_data_type=">h",
    modbus_register_scale=1.0,
    value_fn=None,
)
ACCURATE_REALTIME_SYSTEM_LOAD_POWER_SENSOR_DESCRIPTION = (
    SajH1MqttSensorEntityDescription(
        key="realtime_system_load_power",
        entity_registry_enabled_default=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        modbus_register_offset=None,
        modbus_register_data_type=None,
        modbus_register_scale=None,
        value_fn=None,
    )
)  # custom implementation
ACCURATE_REALTIME_GRID_STATE_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="realtime_grid_state",
    entity_registry_enabled_default=True,
    device_class=None,
    state_class=None,
    native_unit_of_measurement=None,
    modbus_register_offset=0x142,  # use summary_smart_meter_load_power_1 data
    modbus_register_data_type=">h",
    modbus_register_scale=1.0,
    value_fn=lambda x: None
    if x is None
    else (
        GridState.IMPORTING.value
        if x > 0
        else (GridState.EXPORTING.value if x < 0 else GridState.STANDBY.value)
    ),
)

# Inverter time sensor
INVERTER_TIME_SENSOR_DESCRIPTION = SajH1MqttSensorEntityDescription(
    key="inverter_time",
    entity_registry_enabled_default=True,
    device_class=SensorDeviceClass.TIMESTAMP,
    state_class=None,
    native_unit_of_measurement=None,
    modbus_register_offset=None,
    modbus_register_data_type=None,
    modbus_register_scale=None,
    value_fn=lambda x: None,
)

# fmt: off

# inverter data sensors
SAJ_INVERTER_DATA_SENSOR_DESCRIPTIONS: tuple[SajH1MqttSensorEntityDescription, ...] = (
    SajH1MqttSensorEntityDescription(key="inverter_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_sub_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=2, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_comm_pro_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=4, modbus_register_data_type=">H", modbus_register_scale=0.001, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_serial_number", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=6, modbus_register_data_type=">S20", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_product_code", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=26, modbus_register_data_type=">S20", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_display_sw_version", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=46, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_master_control_sw_version", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=48, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_slave_control_sw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=50, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_display_board_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=52, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_control_board_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=54, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_power_board_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=56, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="inverter_battery_numbers", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=58, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None) # always 0
)

# battery data sensors
SAJ_BATTERY_DATA_SENSOR_DESCRIPTIONS: tuple[SajH1MqttSensorEntityDescription, ...] = (
    SajH1MqttSensorEntityDescription(key="battery_1_bms_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_bms_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=2, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_bms_sw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=18, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_bms_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=20, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=22, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=24, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_bms_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=40, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_bms_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=42, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_bms_sw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=58, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_bms_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=60, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=62, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=64, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_bms_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=80, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_bms_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=82, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_bms_sw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=98, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_bms_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=100, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=102, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=104, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_bms_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=120, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_bms_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=122, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_bms_sw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=138, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_bms_hw_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=140, modbus_register_data_type=">H", modbus_register_scale="0.001", value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=142, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_serial_number", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=144, modbus_register_data_type=">S16", modbus_register_scale=None, value_fn=None)
)

# battery controller data sensors
SAJ_BATTERY_CONTROLLER_DATA_SENSOR_DESCRIPTIONS: tuple[SajH1MqttSensorEntityDescription, ...] = (
    SajH1MqttSensorEntityDescription(key="battery_numbers", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_capacity", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement="AH", modbus_register_offset=2, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_fault", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=4, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_warning", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=6, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_fault", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=8, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_warning", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=10, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_fault", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=12, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_warning", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=14, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_fault", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=16, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_warning", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=18, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    #SajH1MqttSensorEntityDescription(key="controller_reserve", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=20, modbus_register_data_type=">HH", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_soc", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=24, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_soh", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=26, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_voltage", entity_registry_enabled_default=False, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=28, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_current", entity_registry_enabled_default=False, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=30, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_temperature", entity_registry_enabled_default=False, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=32, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_1_cycle_num", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=34, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_soc", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=36, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_soh", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=38, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_voltage", entity_registry_enabled_default=False, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=40, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_current", entity_registry_enabled_default=False, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=42, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_temperature", entity_registry_enabled_default=False, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=44, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_2_cycle_num", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=46, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_soc", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=48, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_soh", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=50, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_voltage", entity_registry_enabled_default=False, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=52, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_current", entity_registry_enabled_default=False, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=54, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_temperature", entity_registry_enabled_default=False, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=56, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_3_cycle_num", entity_registry_enabled_default=False, modbus_register_offset=58, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_soc", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=60, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_soh", entity_registry_enabled_default=False, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=62, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_voltage", entity_registry_enabled_default=False, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=64, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_current", entity_registry_enabled_default=False, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=66, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_temperature", entity_registry_enabled_default=False, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=68, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_4_cycle_num", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=70, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
)

# config data sensors
SAJ_CONFIG_DATA_SENSOR_DESCRIPTIONS: tuple[SajH1MqttSensorEntityDescription, ...] = (
    SajH1MqttSensorEntityDescription(key="app_mode", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: AppMode(x).name),
    SajH1MqttSensorEntityDescription(key="grid_charge_power_limit", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=2, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="grid_feed_power_limit", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=4, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_soc_backup", entity_registry_enabled_default=True, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=84, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_soc_high", entity_registry_enabled_default=True, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=88, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
    SajH1MqttSensorEntityDescription(key="battery_soc_low", entity_registry_enabled_default=True, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=90, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
)

# fmt: on


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SajH1MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities based on a config entry."""
    entities: list[SajH1MqttSensorEntity] = []

    # Check if we want to use the accurate power sensors or not
    use_accurate_realtime_power_data = entry.options.get(
        CONF_ENABLE_ACCURATE_REALTIME_POWER_DATA, False
    )

    # Get coordinators (only realtime data is required, all others are optional)
    coordinator_realtime_data = entry.runtime_data.coordinator_realtime_data
    coordinator_inverter_data = entry.runtime_data.coordinator_inverter_data
    coordinator_battery_data = entry.runtime_data.coordinator_battery_data
    coordinator_battery_controller_data = (
        entry.runtime_data.coordinator_battery_controller_data
    )
    coordinator_config_data = entry.runtime_data.coordinator_config_data

    # Realtime data sensors
    for description in SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS:
        entity = SajH1MqttSensorEntity(coordinator_realtime_data, description)
        entities.append(entity)

    # Realtime data energy statistics sensors
    for description in SAJ_REALTIME_DATA_ENERGY_STATS_SENSOR_DESCRIPTIONS:
        # 4 statistics for each type
        stats_offset = description.modbus_register_offset
        for period in "daily", "monthly", "yearly", "total":
            # Create new statistics sensor entity description for every period
            stats_description = SajH1MqttSensorEntityDescription(
                key=f"{description.key}_{period}",
                entity_registry_enabled_default=description.entity_registry_enabled_default,
                device_class=description.device_class,
                state_class=description.state_class,
                native_unit_of_measurement=description.native_unit_of_measurement,
                modbus_register_offset=stats_offset,
                modbus_register_data_type=description.modbus_register_data_type,
                modbus_register_scale=description.modbus_register_scale,
                value_fn=description.value_fn,
            )
            entity = SajH1MqttSensorEntity(coordinator_realtime_data, stats_description)
            entities.append(entity)
            # Update offset for next period
            stats_offset += 4

    # Realtime power sensors

    # Realtime pv power sensor
    entity = SajH1MqttSensorEntity(
        coordinator_realtime_data, REALTIME_PV_POWER_SENSOR_DESCRIPTION
    )
    entities.append(entity)

    # Realtime battery power sensor
    entity = SajH1MqttSensorEntity(
        coordinator_realtime_data, REALTIME_BATTERY_POWER_SENSOR_DESCRIPTION
    )
    entities.append(entity)

    # Realtime grid power sensor (use default or accurate power data)
    description = REALTIME_GRID_POWER_SENSOR_DESCRIPTION
    if use_accurate_realtime_power_data:
        description = ACCURATE_REALTIME_GRID_POWER_SENSOR_DESCRIPTION
    entity = SajH1MqttSensorEntity(coordinator_realtime_data, description)
    entities.append(entity)

    # Realtime system load power sensor (use default or accurate power data)
    if use_accurate_realtime_power_data:
        # Accurate power data must be calculated from different sensors
        entity = SajH1MqttRealtimeSystemLoadPowerSensorEntity(
            coordinator_realtime_data,
            ACCURATE_REALTIME_SYSTEM_LOAD_POWER_SENSOR_DESCRIPTION,
            get_entity_description(
                SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "summary_system_load_power"
            ),
            get_entity_description(
                SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS,
                "summary_smart_meter_load_power_1",
            ),
            get_entity_description(
                SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS,
                "summary_smart_meter_load_power_2",
            ),
        )
        entities.append(entity)
    else:
        entity = SajH1MqttSensorEntity(
            coordinator_realtime_data, REALTIME_SYSTEM_LOAD_POWER_SENSOR_DESCRIPTION
        )
        entities.append(entity)

    # Custom state sensors (based on realtime data)

    # PV state sensor
    entity = SajH1MqttSensorEntity(
        coordinator_realtime_data, REALTIME_PV_STATE_SENSOR_DESCRIPTION
    )
    entities.append(entity)

    # Battery state sensor
    entity = SajH1MqttSensorEntity(
        coordinator_realtime_data, REALTIME_BATTERY_STATE_SENSOR_DESCRIPTION
    )
    entities.append(entity)

    # Grid state sensor (use default or accurate power data)
    description = REALTIME_GRID_STATE_SENSOR_DESCRIPTION
    if use_accurate_realtime_power_data:
        description = ACCURATE_REALTIME_GRID_STATE_SENSOR_DESCRIPTION
    entity = SajH1MqttSensorEntity(coordinator_realtime_data, description)
    entities.append(entity)

    # System load state sensor
    entity = SajH1MqttSensorEntity(
        coordinator_realtime_data, REALTIME_SYSTEM_LOAD_STATE_SENSOR_DESCRIPTION
    )
    entities.append(entity)

    # Inverter time sensor (based on multiple realtime data registers)
    entity = SajH1MqttInverterTimeSensorEntity(
        coordinator_realtime_data,
        INVERTER_TIME_SENSOR_DESCRIPTION,
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_year"),
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_month"),
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_day"),
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_hour"),
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_minute"),
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_second"),
        get_entity_description(SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS, "time_reserved"),
        hass.config.time_zone,  # Time zone for constructing time with correct time zone
    )
    entities.append(entity)

    # Inverter data sensors
    if coordinator_inverter_data:
        for description in SAJ_INVERTER_DATA_SENSOR_DESCRIPTIONS:
            entity = SajH1MqttSensorEntity(coordinator_inverter_data, description)
            entities.append(entity)

    # Battery data sensors
    if coordinator_battery_data:
        for description in SAJ_BATTERY_DATA_SENSOR_DESCRIPTIONS:
            entity = SajH1MqttSensorEntity(coordinator_battery_data, description)
            entities.append(entity)

    # Battery controller data sensors
    if coordinator_battery_controller_data:
        for description in SAJ_BATTERY_CONTROLLER_DATA_SENSOR_DESCRIPTIONS:
            entity = SajH1MqttSensorEntity(
                coordinator_battery_controller_data, description
            )
            entities.append(entity)

    # Config data sensors
    if coordinator_config_data:
        for description in SAJ_CONFIG_DATA_SENSOR_DESCRIPTIONS:
            entity = SajH1MqttSensorEntity(coordinator_config_data, description)
            entities.append(entity)

    # Add the entities
    LOGGER.info(f"Setting up {len(entities)} sensor entities")
    async_add_entities(entities)


class SajH1MqttSensorEntity(SajH1MqttEntity, SensorEntity):
    """SAJ H1 MQTT sensor entity."""

    @property
    def _entity_type(self) -> str:
        return "sensor"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the native value to represent the entity state."""
        return self._get_native_value()


class SajH1MqttRealtimeSystemLoadPowerSensorEntity(SajH1MqttSensorEntity):
    """SAJ H1 MQTT realtime system load power sensor entity.

    This custom sensor uses the value of 2 smart meter sensors to calculate the final value.
    """

    def __init__(
        self,
        coordinator: SajH1MqttDataCoordinator,
        description: SajH1MqttEntityDescription,
        system_load: SajH1MqttEntityDescription,
        smart_meter_1: SajH1MqttEntityDescription,
        smart_meter_2: SajH1MqttEntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description)
        self._system_load = SajH1MqttSensorEntity(coordinator, system_load)
        self._smart_meter_1 = SajH1MqttSensorEntity(coordinator, smart_meter_1)
        self._smart_meter_2 = SajH1MqttSensorEntity(coordinator, smart_meter_2)

    def _get_system_load_power(self) -> int | float | str | None:
        """Get the system load power sensor value."""
        val = self._system_load.native_value
        return val if val else 0.0

    def _get_smart_meter_1_power(self) -> int | float | str | None:
        """Get the smart meter 1 power sensor value."""
        val = self._smart_meter_1.native_value
        return val if val else 0.0

    def _get_smart_meter_2_power(self) -> int | float | str | None:
        """Get the smart meter 2 power sensor value."""
        val = self._smart_meter_2.native_value
        return val if val else 0.0

    def _get_native_value(self) -> int | float | str | None:
        """Get the native value for the entity.

        The realtime system load power sensor is the sum of:
        - the system load power
        - the smart meter 1 power
        - the smart meter 2 power (which is inverted, so we can just add it)
        """
        # Return None if no coordinator data
        payload = self.coordinator.data
        if payload is None:
            return None

        value = (
            self._get_system_load_power()
            + self._get_smart_meter_1_power()
            + self._get_smart_meter_2_power()
        )

        LOGGER.debug(
            f"Entity: {self.entity_id}, value: {value}{' ' + self.unit_of_measurement if self.unit_of_measurement else ''}"
        )

        return value


class SajH1MqttInverterTimeSensorEntity(SajH1MqttSensorEntity):
    """SAJ H1 MQTT inverter time sensor entity.

    This custom sensor uses the values of different time registers to construct the time.
    """

    def __init__(
        self,
        coordinator: SajH1MqttDataCoordinator,
        description: SajH1MqttEntityDescription,
        year: SajH1MqttEntityDescription,
        month: SajH1MqttEntityDescription,
        day: SajH1MqttEntityDescription,
        hour: SajH1MqttEntityDescription,
        minute: SajH1MqttEntityDescription,
        second: SajH1MqttEntityDescription,
        reserved: SajH1MqttEntityDescription,
        time_zone: str | None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, description)
        self._year = SajH1MqttSensorEntity(coordinator, year)
        self._month = SajH1MqttSensorEntity(coordinator, month)
        self._day = SajH1MqttSensorEntity(coordinator, day)
        self._hour = SajH1MqttSensorEntity(coordinator, hour)
        self._minute = SajH1MqttSensorEntity(coordinator, minute)
        self._second = SajH1MqttSensorEntity(coordinator, second)
        self._reserved = SajH1MqttSensorEntity(coordinator, reserved)
        self._zone_info = ZoneInfo(time_zone or "UTC")  # fallback to UTC

    def _get_native_value(self) -> int | float | str | None:
        """Get the native value for the entity.

        The datetime is constructed from the different time registers.
        """
        # Return None if no coordinator data
        payload = self.coordinator.data
        if payload is None:
            return None

        # Get different time register values
        yyyy = self._year.native_value
        mm = self._month.native_value
        dd = self._day.native_value
        hh = self._hour.native_value
        mi = self._minute.native_value
        ss = self._second.native_value

        # Create timezone aware datetime
        value = None
        if all(x is not None for x in [yyyy, mm, dd, hh, mi, ss]):
            value = datetime(yyyy, mm, dd, hh, mi, ss, tzinfo=self._zone_info)

        LOGGER.debug(
            f"Entity: {self.entity_id}, value: {value}{' ' + self.unit_of_measurement if self.unit_of_measurement else ''}"
        )

        return value
