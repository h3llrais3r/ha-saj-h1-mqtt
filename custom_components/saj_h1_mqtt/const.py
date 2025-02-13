"""Constants for the SAJ H1 MQTT integration."""

from __future__ import annotations

from datetime import timedelta
from enum import Enum
import logging

DOMAIN = "saj_h1_mqtt"
BRAND = "SAJ"
MANUFACTURER = "SAJ Electric"
MODEL = "H1 series inverter"
MODEL_SHORT = "H1"

# Configuration constants
CONF_SERIAL_NUMBER = "serial_number"
CONF_SCAN_INTERVAL_REALTIME_DATA = "scan_interval_realtime_data"
CONF_SCAN_INTERVAL_INVERTER_DATA = "scan_interval_inverter_data"
CONF_SCAN_INTERVAL_BATTERY_DATA = "scan_interval_battery_data"
CONF_SCAN_INTERVAL_BATTERY_CONTROLLER_DATA = "scan_interval_battery_controller_data"
CONF_SCAN_INTERVAL_CONFIG_DATA = "scan_interval_config_data"
CONF_ENABLE_SERIAL_NUMBER_PREFIX = "enable_serial_number_prefix"
CONF_ENABLE_ACCURATE_REALTIME_POWER_DATA = "enable_accurate_realtime_power_data"
CONF_ENABLE_MQTT_DEBUG = "enable_mqtt_debug"

# Service constants
SERVICE_READ_REGISTER = "read_register"
SERVICE_WRITE_REGISTER = "write_register"
SERVICE_REFRESH_INVERTER_DATA = "refresh_inverter_data"
SERVICE_REFRESH_BATTERY_DATA = "refresh_battery_data"
SERVICE_REFRESH_BATTERY_CONTROLLER_DATA = "refresh_battery_controller_data"
SERVICE_REFRESH_CONFIG_DATA = "refresh_config_data"

# Attribute constants
ATTR_CONFIG_ENTRY = "config_entry"
ATTR_REGISTER = "register"
ATTR_REGISTER_FORMAT = "register_format"
ATTR_REGISTER_SIZE = "register_size"
ATTR_REGISTER_VALUE = "register_value"
ATTR_APP_MODE = "app_mode"

# Modbus constants
MODBUS_MAX_REGISTERS_PER_QUERY = (
    0x64  # Absolute max is 123 (0x7b) registers per MQTT packet request (do not exceed)
)
MODBUS_DEVICE_ADDRESS = 0x01
MODBUS_READ_REQUEST = 0x03
MODBUS_WRITE_REQUEST = 0x06

# Modbus registers
MODBUS_REG_APP_MODE = 0x3247
MODBUS_REG_GRID_CHARGE_POWER_LIMIT = 0x3248
MODBUS_REG_GRID_FEED_POWER_LIMIT = 0x3249
MODBUS_REG_BATTERY_SOC_BACKUP = 0x3271
MODBUS_REG_BATTERY_SOC_HIGH = 0x3273
MODBUS_REG_BATTERY_SOC_LOW = 0x3274

# Mqtt constants
MQTT_QOS = 2
MQTT_RETAIN = False
MQTT_ENCODING = None
MQTT_DATA_TRANSMISSION = "data_transmission"
MQTT_DATA_TRANSMISSION_RSP = "data_transmission_rsp"
MQTT_DATA_TRANSMISSION_TIMEOUT = 10

# Default constants
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

LOGGER = logging.getLogger(__package__)


class WorkingMode(Enum):
    """Working mode."""

    WAIT = 1
    NORMAL = 2
    FAULT = 3
    UPDATE = 4


class AppMode(Enum):
    """App mode."""

    SELF_USE = 0
    TIME_OF_USE = 1
    BACKUP = 2
    PASSIVE = 3


class SolarState(Enum):
    """Solar state."""

    PRODUCING = "PRODUCING"
    STANDBY = "STANDBY"


class BatteryState(Enum):
    "Battery state."

    CHARGING = "CHARGING"
    DISCHARGING = "DISCHARGING"
    STANDBY = "STANDBY"


class GridState(Enum):
    """Grid state."""

    IMPORTING = "IMPORTING"
    EXPORTING = "EXPORTING"
    STANDBY = "STANDBY"


class SystemLoadState(Enum):
    "System load state."

    CONSUMING = "CONSUMING"
    STANDBY = "STANDBY"
