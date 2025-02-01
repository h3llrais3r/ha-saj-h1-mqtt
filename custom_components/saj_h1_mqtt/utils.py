"""Utility functions for the SAJ H1 MQTT integration."""

from .const import LOGGER


def log_hex(value: int) -> str:
    """Log a value in hexadecimal and numeric format."""
    return f"{hex(value)} ({value})"


def debug(msg: str, enabled: bool = True) -> None:
    """Debug log helper to decide if it shoud be logged or not."""
    if enabled:
        LOGGER.debug(msg)
