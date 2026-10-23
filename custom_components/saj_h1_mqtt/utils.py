"""Utility functions for the SAJ H1 MQTT integration."""

from .const import LOGGER


def log_hex(value: int) -> str:
    """Log a value in hexadecimal and numeric format."""
    return f"{hex(value)} ({value})"


def debug(msg: str, enabled: bool = True) -> None:
    """Debug log helper to decide if it shoud be logged or not."""
    if enabled:
        LOGGER.debug(msg)


def computeCRC(data: bytes) -> int:
    """Compute a crc16 on the passed in string.

    For modbus, this is only used on the binary serial protocols (in this case RTU).

    The difference between modbus's crc16 and a normal crc16 is that modbus starts the crc value out at 0xffff.

    Replacement for pymodbus.utilities.computeCRC(...)
    Taken from: https://stackoverflow.com/questions/69369408/calculating-crc16-in-python-for-modbus
    Adapted to swap buffers

    :param data: The data to create a crc16 of
    :returns: The calculated CRC
    """
    crc = 0xFFFF
    for data_byte in data:
        crc ^= data_byte
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return ((crc & 0xFF) << 8) | (crc >> 8)


def decode_times_enabled_register(x: int) -> str:
    """Decode a time enabled register from a bitmask.

    Each bit represents one of the 7 configured time slots.
    Enabled slots are represented by their numbers; disabled slots are omitted.

    Examples:
        x = 0   -> "0"
        x = 5   -> "1,3"
        x = 127 -> "1,2,3,4,5,6,7"
    """
    enabled_slots = [str(i + 1) for i in range(7) if x & (1 << i)]
    return ",".join(enabled_slots) if enabled_slots else "0"


def decode_time_register(x: int) -> str:
    """Decode a time register into HH:MM format.

    The high byte represents the hour and the low byte represents the minute.

    Example:
        x = 0x0000 -> "00:00"
        x = 0x173B -> "23:59"
    """
    return f"{(x >> 8) & 0xFF:02d}:{x & 0xFF:02d}"


def decode_charge_time_power_register(x: int) -> str:
    """Decode a charge time power register into power percentage and enabled days.

    The high byte is a bitmask for the days of the week (bit 0 = Monday, bit 1 = Tuesday, ..., bit 6 = Sunday).
    The low byte represents the power percentage.

    Examples:
        x = 0x0000 -> "0%"
        x = 0x150A -> "10% (Mo,We,Fr)"
        x = 0x7F14 -> "20% (Mo,Tu,We,Th,Fr,Sa,Su)"
    """
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    enabled_days = [day for i, day in enumerate(days) if x & (1 << (8 + i))]

    power = x & 0xFF
    return f"{power}%" + (f" ({','.join(enabled_days)})" if enabled_days else "")
