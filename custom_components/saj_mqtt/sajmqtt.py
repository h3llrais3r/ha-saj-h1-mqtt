"""SAJ MQTT inverter client."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
import contextlib
from datetime import datetime
from random import random
from struct import pack, unpack_from

from pymodbus.utilities import computeCRC

from homeassistant.components.mqtt import ReceiveMessage
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import (
    LOGGER,
    MODBUS_DEVICE_ADDRESS,
    MODBUS_MAX_REGISTERS_PER_QUERY,
    MODBUS_READ_REQUEST,
    MODBUS_WRITE_REQUEST,
    SAJ_MQTT_DATA_TRANSMISSION,
    SAJ_MQTT_DATA_TRANSMISSION_RSP,
    SAJ_MQTT_DATA_TRANSMISSION_TIMEOUT,
    SAJ_MQTT_QOS,
)


class SajMqtt:
    """SAJ MQTT inverter client instance."""

    def __init__(self, hass: HomeAssistant, serial_number: str) -> None:
        """Set up the SajMqtt class."""
        super().__init__()

        self.hass = hass
        self.mqtt = hass.components.mqtt
        self.serial_number = serial_number
        self.topic_data_transmission = (
            f"saj/{self.serial_number}/{SAJ_MQTT_DATA_TRANSMISSION}"
        )
        self.topic_data_transmission_rsp = (
            f"saj/{self.serial_number}/{SAJ_MQTT_DATA_TRANSMISSION_RSP}"
        )

        self.query_responses = OrderedDict()
        self.write_responses = OrderedDict()

        self.unsubscribe_callbacks = {}

    async def initialize(self) -> None:
        """Initialize."""
        self.unsubscribe_callbacks = await self._subscribe_topics()

    async def deinitialize(self) -> None:
        """Deinitialize.

        Currently not used, as we set up via async_setup_platform(), which doesn't support unloading
        """
        for unsubscribe_callback in self.unsubscribe_callbacks.values():
            await unsubscribe_callback()

    async def read_realtime_data(
        self,
        start_register: int,
        count: int,
        timeout: int = SAJ_MQTT_DATA_TRANSMISSION_TIMEOUT,
    ) -> bytearray | None:
        """Read the realtime data registers from the inverter.

        This method hides all the package splitting and returns the raw bytes if successful.
        It returns None in case data could not be retrieved in time.
        """
        LOGGER.debug("Reading realtime data")
        self.query_responses.clear()  # clear previous responses

        # Create the MQTT data_transmission packets to send to the inverter
        packets: list[tuple[bytes, int]] = []
        while count > 0:
            regs_count = min(count, MODBUS_MAX_REGISTERS_PER_QUERY)
            packet = self._create_mqtt_read_packet(start_register, regs_count)
            packets.append(packet)
            start_register += regs_count
            count -= regs_count
        try:
            async with asyncio.timeout(timeout):
                # Publish the packets
                for packet, req_id in packets:
                    self.query_responses[req_id] = None
                    LOGGER.debug(
                        f"Publishing packet with request id: {f'{req_id:04x}'}"
                    )
                    await self.mqtt.async_publish(
                        self.hass,
                        self.topic_data_transmission,
                        packet,
                        qos=2,
                        retain=False,
                        encoding=None,
                    )
                LOGGER.debug("All packets published")

                # Wait for the answer packets
                while True:
                    LOGGER.debug(
                        f"Waiting for responses with request id: {[f'{k:04x}' for k,v in self.query_responses.items() if v is None]}"
                    )
                    if all(self.query_responses.values()) is True:
                        break
                    await asyncio.sleep(1)
                LOGGER.debug("All responses received")

                # Concatenate the payloads, so we get the full answer
                data = bytearray()
                for response in self.query_responses.values():
                    data += response

        except asyncio.TimeoutError:
            LOGGER.warning(
                "Timeout error: the inverter did not answer in the expected timeout"
            )
            data = None
        except HomeAssistantError as ex:
            LOGGER.warning(
                f"Could not publish {SAJ_MQTT_DATA_TRANSMISSION} packets, reason: {ex}"
            )
            data = None

        # Cleanup self.query_responses from request ids generated in this method
        for _, req_id in packets:
            with contextlib.suppress(KeyError):
                del self.query_responses[req_id]

        return data

    async def write_register(
        self,
        register: int,
        value: int,
        timeout: int = SAJ_MQTT_DATA_TRANSMISSION_TIMEOUT,
    ) -> int | None:
        """Write a register value to the inverter."""
        LOGGER.debug(f"Writing inverter register {register:04x}: {value:02x}")

        # Create the MQTT data_transmission packet to send to the inverter
        packet, req_id = self._create_mqtt_write_packet(register, value)
        try:
            async with asyncio.timeout(timeout):
                # Publish packet
                self.write_responses[req_id] = None
                LOGGER.debug(f"Publishing packet with request id: {f'{req_id:04x}'}")
                await self.mqtt.async_publish(
                    self.hass,
                    self.topic_data_transmission,
                    packet,
                    qos=2,
                    retain=False,
                    encoding=None,
                )

                # Wait for the answer packet
                while True:
                    LOGGER.debug(
                        f"Waiting for response with request id: {f'{req_id:04x}' if self.write_responses[req_id] is None else ''}"
                    )
                    if self.write_responses[req_id]:
                        break
                    await asyncio.sleep(1)
                LOGGER.debug("Response received")

                # Concatenate the payloads, so we get the full answer
                data = self.write_responses[req_id]

        except asyncio.TimeoutError:
            LOGGER.warning(
                "Timeout error: the inverter did not answer in expected timeout"
            )
            data = None
        except HomeAssistantError as ex:
            LOGGER.warning(
                f"Could not publish {SAJ_MQTT_DATA_TRANSMISSION} packets, reason: {ex}"
            )
            data = None

        # Cleanup self.write_responses from request id generated in this method
        with contextlib.suppress(KeyError):
            del self.write_responses[req_id]

        return data

    async def _subscribe_topics(self) -> dict:
        """Subscribe to MQTT topics."""
        topics = {
            SAJ_MQTT_DATA_TRANSMISSION_RSP: {
                "topic": self.topic_data_transmission_rsp,
                "msg_callback": self._handle_data_transmission_rsp,
                "qos": SAJ_MQTT_QOS,
                "encoding": None,
            }
        }

        LOGGER.debug(f"Subscribing to topics: {list(topics.keys())}")
        unsubscribe_callbacks = {}
        for item, topic_data in topics.items():
            unsubscribe_callbacks[item] = await self.mqtt.async_subscribe(
                topic_data["topic"],
                topic_data["msg_callback"],
                qos=topic_data["qos"],
                encoding=topic_data["encoding"],
            )

        return unsubscribe_callbacks

    @callback
    def _handle_data_transmission_rsp(self, msg: ReceiveMessage) -> None:
        """Handle a single packet received from MQTT."""
        try:
            LOGGER.debug(f"Received {SAJ_MQTT_DATA_TRANSMISSION_RSP} packet")
            req_id, size, content = self._parse_packet(msg.payload)
            if req_id in self.query_responses:
                LOGGER.debug("Required packet for request")
                self.query_responses[req_id] = content
        except Exception as ex:
            LOGGER.error(
                f"Error while handling {SAJ_MQTT_DATA_TRANSMISSION_RSP} packet: {ex}"
            )

    def _parse_packet(self, packet):
        """Parse a mqtt response data_transmission_rsp payload packet.

        Packet consists of [HEADER][SIZE][CONTENT][CRC]:
        - [HEADER] consists of [LENGTH][REQ_ID][TIMESTAMP][REQ_TYPE]
        - [SIZE] of the following content
        - [CONTENT] of the registers
        - [CRC] checksum
        """
        # Get the header
        length, req_id, timestamp, req_type = unpack_from(">HHIH", packet, 0x00)
        req_type -= (
            0x100  # substract 0x100 to match the request type (modbus read or write)
        )
        date = datetime.fromtimestamp(timestamp)

        # Get the size of the content
        (size,) = unpack_from(">B", packet, 0xA)

        # Get the content
        content = packet[0xB : 0xB + size]

        # Get the CRC
        (crc16,) = unpack_from(">H", packet, 0xB + size)

        # CRC is calculated starting from "request" at offset 0x3a
        calc_crc = computeCRC(packet[0x8 : 0xB + size])

        LOGGER.debug(f"Request id: {req_id:04x}")
        LOGGER.debug(f"Request type: {req_type:04x}")
        LOGGER.debug(f"Length: {length} bytes")
        LOGGER.debug(f"Timestamp: {date}")
        LOGGER.debug(f"Register size: {size} bytes")
        LOGGER.debug(f"Register content: {':'.join(f'{byte:02x}' for byte in content)}")
        LOGGER.debug(f"CRC16: {crc16} -> {'ok' if crc16 == calc_crc else 'bad'}")

        return req_id, size, content

    def _create_mqtt_read_packet(self, start: int, count: int) -> tuple[bytes, int]:
        """Create a mqtt read packet.

        Create the data_transmission mqtt body content to read registers from start for the given amount of registers.
        We can query up to 123 registers with a single request.

        Packet consists of [LENTH][HEADER][CONTENT][CRC]:
        - [LENGTH] of [HEADER][CONTENT][CRC]
        - [HEADER] consists of [REQ_ID][0x58][0xC9][RANDOM]
        - [CONTENT] consists of [DEVICE_ADDRESS][REQ_TYPE][REGISTER_START][REGISTER_COUNT]
        - [CRC] checksum
        """
        LOGGER.debug("Creating mqtt read packet")
        content = pack(
            ">BBHH", MODBUS_DEVICE_ADDRESS, MODBUS_READ_REQUEST, start, count
        )

        return self._create_modbus_mqtt_packet(content)

    def _create_mqtt_write_packet(self, register: int, value: int) -> tuple[bytes, int]:
        """Create a mqtt write packet.

        Create the data_transmission mqtt body content to write a value to a register.

        Packet consists of [LENTH][HEADER][CONTENT][CRC]:
        - [LENGTH] of [HEADER][CONTENT][CRC]
        - [HEADER] consists of [REQ_ID][0x58][0xC9][RANDOM]
        - [CONTENT] consists of [DEVICE_ADDRESS][REQ_TYPE][REGISTER_START][REGISTER_COUNT]
        - [CRC] checksum
        """
        LOGGER.debug("Creating mqtt write packet")
        content = pack(
            ">BBHH", MODBUS_DEVICE_ADDRESS, MODBUS_WRITE_REQUEST, register, value
        )

        return self._create_modbus_mqtt_packet(content)

    def _create_modbus_mqtt_packet(self, content: bytes) -> tuple[bytes, int]:
        """Create a modbus mqtt packet.

        The mqtt packet encapsulates the modbus packet to interact with the interter.
        """
        # Compute CRC of modbus content
        crc16 = computeCRC(content)

        # Assemble the modbus content into the mqtt packet framework
        req_id = int(random() * 65536)
        rand = int(random() * 65536)
        packet = pack(">HBBH", req_id, 0x58, 0xC9, rand) + content + pack(">H", crc16)
        LOGGER.debug(
            f"Packet request id: {req_id:04x} - CRC16: {crc16:04x} - random: {rand:04x}"
        )
        LOGGER.debug(f"Packet length: {len(packet)} bytes")
        packet = pack(">H", len(packet)) + packet

        return packet, req_id
