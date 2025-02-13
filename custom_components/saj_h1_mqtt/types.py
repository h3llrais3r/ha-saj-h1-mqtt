"""Types for the SAJ H1 MQTT integration."""

from homeassistant.config_entries import ConfigEntry

from .coordinator import SajH1MqttData

type SajH1MqttConfigEntry = ConfigEntry[SajH1MqttData]
