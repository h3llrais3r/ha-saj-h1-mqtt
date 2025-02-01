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

    For modbus, this is only used on the binary serial protocols (in this
    case RTU).

    The difference between modbus's crc16 and a normal crc16
    is that modbus starts the crc value out at 0xffff.

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
