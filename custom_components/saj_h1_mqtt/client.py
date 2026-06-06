"""Client for the SAJ H1 MQTT integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from collections import OrderedDict
import contextlib
from datetime import datetime
from random import random
from struct import pack, unpack_from

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.components import mqtt
from homeassistant.components.mqtt import ReceiveMessage
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import (
    BRAND,
    LOGGER,
    MODBUS_DEVICE_ADDRESS,
    MODBUS_MAX_REGISTERS,
    MODBUS_READ_ERROR,
    MODBUS_READ_REQUEST,
    MODBUS_RETRY_COUNT,
    MODBUS_RETRY_DELAY,
    MODBUS_TIMEOUT,
    MODBUS_WRITE_ERROR,
    MODBUS_WRITE_MULTIPLE_ERROR,
    MODBUS_WRITE_MULTIPLE_REQUEST,
    MODBUS_WRITE_REQUEST,
    MQTT_DATA_TRANSMISSION,
    MQTT_DATA_TRANSMISSION_RSP,
    MQTT_DATA_TRANSMISSION_TIMEOUT,
    MQTT_ENCODING,
    MQTT_QOS,
    MQTT_RETAIN,
    MQTT_WAIT_SLEEP_TIME,
)
from .utils import computeCRC, debug, log_hex


class SajH1Client(ABC):
    """Base SAJ H1 client instance."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Set up the SajH1Client class."""
        super().__init__()

        self.hass = hass

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the client."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the client."""

    @abstractmethod
    async def read_registers(
        self,
        register_start: int,
        register_count: int,
        register_chunks: list[int] | None = None,
    ) -> bytearray | None:
        """Read 1 or more registers from the inverter."""

    @abstractmethod
    async def write_register(self, register: int, value: int) -> int | None:
        """Write a register value to the inverter."""

    @abstractmethod
    async def write_registers(
        self,
        register_start: int,
        values: list[int],
    ) -> int | None:
        """Write multiple register values to the inverter."""


class SajH1MqttClient(SajH1Client):
    """SAJ H1 MQTT client instance."""

    def __init__(
        self, hass: HomeAssistant, serial_number: str, mqtt_debug: bool = False
    ) -> None:
        """Set up the SajH1MqttClient class."""
        super().__init__(hass)

        self.mqtt = mqtt
        self.serial_number = serial_number
        self._debug = mqtt_debug
        self.topic_data_transmission = (
            f"{BRAND.lower()}/{self.serial_number}/{MQTT_DATA_TRANSMISSION}"
        )
        self.topic_data_transmission_rsp = (
            f"{BRAND.lower()}/{self.serial_number}/{MQTT_DATA_TRANSMISSION_RSP}"
        )

        self.read_responses = OrderedDict()
        self.write_responses = OrderedDict()
        self.write_multiple_responses = OrderedDict()

        self.unsubscribe_callbacks = {}

    async def connect(self) -> None:
        """Connect to mqtt."""
        self.unsubscribe_callbacks = await self._subscribe_topics()

    async def disconnect(self) -> None:
        """Disconnect from mqtt."""
        for topic, unsubscribe_callback in self.unsubscribe_callbacks.items():
            # Unsubscribe callbacks are not async, so no need to await for them
            debug(f"Unsubscribing from topic: {topic}")
            unsubscribe_callback()

    async def read_registers(
        self,
        register_start: int,
        register_count: int,
        register_chunks: list[int] | None = None,
        timeout: int = MQTT_DATA_TRANSMISSION_TIMEOUT,
    ) -> bytearray | None:
        """Read 1 or more registers from the inverter.

        We can read up to 123 registers with a single request.
        Because a modbus mqtt response cannot exceed 256 bytes. (123 registers = 246 bytes, plus some overhead)
        This method hides all the package splitting and returns the raw bytes if successful.
        You can also specify the register_chunks, so you can group the registers that belong together.
        It returns None in case data could not be retrieved in time.
        """
        debug(
            f"Reading registers at {log_hex(register_start)}, length: {log_hex(register_count)}"
        )

        # Create the MQTT data_transmission packets to send to the inverter
        packets: list[tuple[bytes, int]] = []
        chunk_idx = 0
        while register_count > 0:
            if register_chunks:
                # If register_chunks are provided, we need to split the requests according to the chunks
                reg_count = register_chunks[chunk_idx]
                chunk_idx += 1
            else:
                # If no register_chunks are provided, split in chunks of max MODBUS_MAX_REGISTERS registers
                reg_count = min(register_count, MODBUS_MAX_REGISTERS)
            packet = self._create_mqtt_read_packet(register_start, reg_count)
            packets.append(packet)
            register_start += reg_count
            register_count -= reg_count
        try:
            async with asyncio.timeout(timeout):
                # Publish the packets
                req_ids = []
                for packet, req_id in packets:
                    req_ids.append(req_id)
                    self.read_responses[req_id] = None
                    debug(
                        f"Publishing packet with request id: {f'{log_hex(req_id)}'}",
                        self._debug,
                    )
                    await self.mqtt.async_publish(
                        self.hass,
                        self.topic_data_transmission,
                        packet,
                        qos=MQTT_QOS,
                        retain=MQTT_RETAIN,
                        encoding=MQTT_ENCODING,
                    )
                debug("All packets published", self._debug)

                # Wait for the answer packets
                while True:
                    responses = OrderedDict(
                        (k, self.read_responses[k])
                        for k in req_ids
                        if k in self.read_responses
                    )
                    # Check if all responses are returned
                    if all(responses.values()) is True:
                        break
                    debug(
                        f"Waiting for responses with request id: {[f'{log_hex(k)}' for k in req_ids if responses[k] is None]}",
                        self._debug,
                    )
                    await asyncio.sleep(MQTT_WAIT_SLEEP_TIME)
                debug("All responses received", self._debug)

                # Concatenate the payloads, so we get the full answer
                data = bytearray()
                for response in responses.values():
                    data += response
        except TimeoutError:
            LOGGER.warning(
                "Timeout error: the inverter did not answer in the expected timeout"
            )
            data = None
        except HomeAssistantError as ex:
            LOGGER.warning(
                f"Could not publish {MQTT_DATA_TRANSMISSION} packets, reason: {ex}"
            )
            data = None

        # Remove req_ids from self.read_responses
        for req_id in req_ids:
            with contextlib.suppress(KeyError):
                del self.read_responses[req_id]

        return data

    async def write_register(
        self,
        register: int,
        value: int,
        timeout: int = MQTT_DATA_TRANSMISSION_TIMEOUT,
    ) -> int | None:
        """Write a register value to the inverter."""
        debug(f"Writing register at {log_hex(register)}, value: {log_hex(value)}")

        # Create the MQTT data_transmission packet to send to the inverter
        packet, req_id = self._create_mqtt_write_packet(register, value)
        try:
            async with asyncio.timeout(timeout):
                # Publish packet
                self.write_responses[req_id] = None
                debug(
                    f"Publishing packet with request id: {f'{log_hex(req_id)}'}",
                    self._debug,
                )
                await self.mqtt.async_publish(
                    self.hass,
                    self.topic_data_transmission,
                    packet,
                    qos=MQTT_QOS,
                    retain=MQTT_RETAIN,
                    encoding=MQTT_ENCODING,
                )

                # Wait for the answer packet
                while True:
                    # Check if not None, as we can also get 0 as response
                    if self.write_responses[req_id] is not None:
                        break
                    debug(
                        f"Waiting for response with request id: {f'{log_hex(req_id)}' if self.write_responses[req_id] is None else ''}",
                        self._debug,
                    )
                    await asyncio.sleep(MQTT_WAIT_SLEEP_TIME)
                debug("Response received", self._debug)

                # Get the answer
                data = self.write_responses[req_id]
        except TimeoutError:
            LOGGER.warning(
                "Timeout error: the inverter did not answer in expected timeout"
            )
            data = None
        except HomeAssistantError as ex:
            LOGGER.warning(
                f"Could not publish {MQTT_DATA_TRANSMISSION} packets, reason: {ex}"
            )
            data = None

        # Cleanup self.write_responses from request id generated in this method
        with contextlib.suppress(KeyError):
            del self.write_responses[req_id]

        return data

    async def write_registers(
        self,
        register_start: int,
        values: list[int],
        timeout: int = MQTT_DATA_TRANSMISSION_TIMEOUT,
    ) -> int | None:
        """Write multiple register values to the inverter."""
        count = len(values)
        hex_values = ", ".join(log_hex(v) for v in values)
        debug(
            f"Writing register(s) at {log_hex(register_start)}, length: {log_hex(count)}, values: {hex_values}"
        )

        # Create the MQTT data_transmission packet to send to the inverter
        packet, req_id = self._create_mqtt_write_multiple_packet(register_start, values)
        try:
            async with asyncio.timeout(timeout):
                # Publish packet
                self.write_multiple_responses[req_id] = None
                debug(
                    f"Publishing packet with request id: {f'{log_hex(req_id)}'}",
                    self._debug,
                )
                await self.mqtt.async_publish(
                    self.hass,
                    self.topic_data_transmission,
                    packet,
                    qos=MQTT_QOS,
                    retain=MQTT_RETAIN,
                    encoding=MQTT_ENCODING,
                )

                # Wait for the answer packet
                while True:
                    # Check if not None, as we can also get 0 as response
                    if self.write_multiple_responses[req_id] is not None:
                        break
                    debug(
                        f"Waiting for response with request id: {f'{log_hex(req_id)}' if self.write_multiple_responses[req_id] is None else ''}",
                        self._debug,
                    )
                    await asyncio.sleep(MQTT_WAIT_SLEEP_TIME)
                debug("Response received", self._debug)

                # Get the answer
                data = self.write_multiple_responses[req_id]
        except TimeoutError:
            LOGGER.warning(
                "Timeout error: the inverter did not answer in expected timeout"
            )
            data = None
        except HomeAssistantError as ex:
            LOGGER.warning(
                f"Could not publish {MQTT_DATA_TRANSMISSION} packets, reason: {ex}"
            )
            data = None

        # Cleanup self.write_responses from request id generated in this method
        with contextlib.suppress(KeyError):
            del self.write_multiple_responses[req_id]

        return data

    async def _subscribe_topics(self) -> dict:
        """Subscribe to mqtt topics."""
        topics = {
            MQTT_DATA_TRANSMISSION_RSP: {
                "topic": self.topic_data_transmission_rsp,
                "msg_callback": self._handle_data_transmission_rsp,
                "qos": MQTT_QOS,
                "encoding": MQTT_ENCODING,
            }
        }

        unsubscribe_callbacks = {}
        for topic_data in topics.values():
            topic = topic_data["topic"]
            debug(f"Subscribing to topic: {topic}")
            unsubscribe_callbacks[topic] = await self.mqtt.async_subscribe(
                self.hass,
                topic,
                topic_data["msg_callback"],
                qos=topic_data["qos"],
                encoding=topic_data["encoding"],
            )

        return unsubscribe_callbacks

    @callback
    def _handle_data_transmission_rsp(self, msg: ReceiveMessage) -> None:
        """Handle a mqtt data_transmission_rsp response packet."""
        try:
            debug(f"Received {MQTT_DATA_TRANSMISSION_RSP} packet", self._debug)
            req_id, content = self._parse_packet(msg.payload)
            if req_id in self.read_responses:
                self.read_responses[req_id] = content
            elif req_id in self.write_responses:
                self.write_responses[req_id] = content
            elif req_id in self.write_multiple_responses:
                self.write_multiple_responses[req_id] = content
            else:
                debug("Response packet not expected, ignoring it", self._debug)
        except Exception as ex:  # noqa: BLE001
            LOGGER.error(
                f"Error while handling {MQTT_DATA_TRANSMISSION_RSP} packet: {ex}"
            )

    def _parse_packet(self, packet) -> tuple[int, bytearray | int]:
        """Parse a mqtt packet.

        Packet consists of [HEADER][PACKET_DATA]:
        - [HEADER] consists of [LENGTH][REQ_ID][TIMESTAMP][DEVICE_ADDRESS][REQ_TYPE]
        - [PACKET_DATA] see specific packet parsing
        """
        # Parse the header
        length, req_id, timestamp, device_address, req_type = unpack_from(
            ">HHIBB", packet, 0x00
        )
        date = datetime.fromtimestamp(timestamp)

        debug(f"Response bytes: {':'.join(f'{b:02x}' for b in packet)}", self._debug)
        debug(f"Request id: {log_hex(req_id)}", self._debug)
        debug(f"Device address: {log_hex(device_address)}", self._debug)
        debug(f"Request type: {log_hex(req_type)}", self._debug)
        debug(f"Length: {length} bytes", self._debug)
        debug(f"Timestamp: {date}", self._debug)

        if req_type == MODBUS_READ_REQUEST:
            content = self._parse_read_packet(packet)
        elif req_type == MODBUS_WRITE_REQUEST:
            content = self._parse_write_packet(packet)
        elif req_type == MODBUS_WRITE_MULTIPLE_REQUEST:
            content = self._parse_write_multiple_packet(packet)
        elif req_type in [
            MODBUS_READ_ERROR,
            MODBUS_WRITE_ERROR,
            MODBUS_WRITE_MULTIPLE_ERROR,
        ]:
            content = self._parse_error_packet(packet)
            raise ValueError(f"Modbus error code: {log_hex(content)}")
        else:
            raise ValueError(f"Unsupported request type: {log_hex(req_type)}")

        return req_id, content

    def _parse_read_packet(self, packet) -> bytearray:
        """Parse a mqtt read packet.

        Packet consists of [SIZE][CONTENT][CRC]:
        - [SIZE] of the following content
        - [CONTENT] of the registers
        - [CRC] checksum
        """
        # Get the size of the content
        (size,) = unpack_from(">B", packet, 0xA)

        # Get the content
        content = packet[0xB : 0xB + size]

        # Get the CRC
        (crc,) = unpack_from(">H", packet, 0xB + size)

        # CRC is calculated starting from "request" at offset 0x3a
        calc_crc = computeCRC(packet[0x8 : 0xB + size])

        debug(f"Content length: {size} bytes", self._debug)
        debug(f"Content bytes: {':'.join(f'{b:02x}' for b in content)}", self._debug)
        debug(
            f"CRC: {log_hex(crc)} -> {'ok' if crc == calc_crc else 'bad'}",
            self._debug,
        )

        if crc != calc_crc:
            raise ValueError("Invalid CRC: expected {calc_crc}, received {crc}")

        return content

    def _parse_write_packet(self, packet) -> int:
        """Parse a mqtt write packet.

        Packet consists of [REGISTER][VALUE][CRC]:
        - [REGISTER] to which the value was written
        - [VALUE] written to the register
        - [CRC] checksum
        """
        register, value, orig_crc = unpack_from(">HHH", packet, 0xA)  # noqa: RUF059

        # Get the CRC
        (crc,) = unpack_from(">H", packet, 0xE)

        # CRC is calculated starting from "request" at offset 0x3a
        calc_crc = computeCRC(packet[0x8:0xE])

        debug(f"Written register: {log_hex(register)}", self._debug)
        debug(f"Written value: {log_hex(value)}", self._debug)
        debug(
            f"CRC: {log_hex(crc)} -> {'ok' if crc == calc_crc else 'bad'}",
            self._debug,
        )

        if crc != calc_crc:
            raise ValueError("Invalid CRC: expected {calc_crc}, received {crc}")

        return value

    def _parse_write_multiple_packet(self, packet) -> int:
        """Parse a mqtt write multiple packet.

        Packet consists of [REGISTER_START][COUNT][CRC]:
        - [REGISTER_START] the first register written
        - [COUNT] the number of registers written
        - [CRC] checksum
        """
        register_start, count, orig_crc = unpack_from(">HHH", packet, 0xA)  # noqa: RUF059

        # Get the CRC
        (crc,) = unpack_from(">H", packet, 0xE)

        # CRC is calculated starting from "request" at offset 0x3a
        calc_crc = computeCRC(packet[0x8:0xE])

        debug(f"First register written: {log_hex(register_start)}", self._debug)
        debug(f"Number of registers written: {log_hex(count)}", self._debug)
        debug(
            f"CRC: {log_hex(crc)} -> {'ok' if crc == calc_crc else 'bad'}",
            self._debug,
        )

        if crc != calc_crc:
            raise ValueError("Invalid CRC: expected {calc_crc}, received {crc}")

        return count

    def _parse_error_packet(self, packet) -> int:
        """Parse a mqtt error packet.

        Packet consists of [ERROR_CODE][CRC]:
        - [ERROR_CODE] the error code
        - [CRC] checksum
        """
        error_code, orig_crc = unpack_from(">BH", packet, 0xA)  # noqa: RUF059

        # Get the CRC
        (crc,) = unpack_from(">H", packet, 0xE)

        # CRC is calculated starting from "request" at offset 0x3a
        calc_crc = computeCRC(packet[0x8:0xE])

        debug(f"Error code: {log_hex(error_code)}", self._debug)
        debug(
            f"CRC: {log_hex(crc)} -> {'ok' if crc == calc_crc else 'bad'}",
            self._debug,
        )

        if crc != calc_crc:
            raise ValueError("Invalid CRC: expected {calc_crc}, received {crc}")

        return error_code

    def _create_mqtt_read_packet(
        self, register_start: int, count: int
    ) -> tuple[bytes, int]:
        """Create a mqtt read packet.

        Create the data_transmission mqtt body content to read registers from start for the given amount of registers.

        Packet consists of [LENTH][HEADER][CONTENT][CRC]:
        - [LENGTH] of [HEADER][CONTENT][CRC]
        - [HEADER] consists of [REQ_ID][0x58][0xC9][RANDOM]
        - [CONTENT] consists of [DEVICE_ADDRESS][REQ_TYPE][REGISTER_START][COUNT]
        - [CRC] checksum
        """
        debug("Creating mqtt read packet", self._debug)
        content = pack(
            ">BBHH", MODBUS_DEVICE_ADDRESS, MODBUS_READ_REQUEST, register_start, count
        )

        return self._create_modbus_mqtt_packet(MODBUS_READ_REQUEST, content)

    def _create_mqtt_write_packet(self, register: int, value: int) -> tuple[bytes, int]:
        """Create a mqtt write packet.

        Create the data_transmission mqtt body content to write a value to a register.

        Packet consists of [LENTH][HEADER][CONTENT][CRC]:
        - [LENGTH] of [HEADER][CONTENT][CRC]
        - [HEADER] consists of [REQ_ID][0x58][0xC9][RANDOM]
        - [CONTENT] consists of [DEVICE_ADDRESS][REQ_TYPE][REGISTER][VALUE]
        - [CRC] checksum
        """
        debug("Creating mqtt write packet", self._debug)
        content = pack(
            ">BBHH", MODBUS_DEVICE_ADDRESS, MODBUS_WRITE_REQUEST, register, value
        )

        return self._create_modbus_mqtt_packet(MODBUS_WRITE_REQUEST, content)

    def _create_mqtt_write_multiple_packet(
        self, register_start: int, values: list[int]
    ) -> tuple[bytes, int]:
        """Create a mqtt write multiple packet.

        Create the data_transmission mqtt body content to write multiple values to a multiple registers.

        Packet consists of [LENTH][HEADER][CONTENT][CRC]:
        - [LENGTH] of [HEADER][CONTENT][CRC]
        - [HEADER] consists of [REQ_ID][0x58][0xC9][RANDOM]
        - [CONTENT] consists of [DEVICE_ADDRESS][REQ_TYPE][REGISTER_START][COUNT][SIZE][VALUES]
        - [CRC] checksum
        """
        debug("Creating mqtt write multiple packet", self._debug)
        count = len(values)
        size = count * 2  # size in bytes (2 bytes per register)
        content = pack(
            ">BBHHB",
            MODBUS_DEVICE_ADDRESS,
            MODBUS_WRITE_MULTIPLE_REQUEST,
            register_start,
            count,
            size,
        )
        # values are always written as 16-bit registers (unsigned short)
        for value in values:
            content += pack(">H", value)

        return self._create_modbus_mqtt_packet(MODBUS_WRITE_MULTIPLE_REQUEST, content)

    def _create_modbus_mqtt_packet(
        self, req_type: int, content: bytes
    ) -> tuple[bytes, int]:
        """Create a modbus mqtt packet.

        The mqtt packet encapsulates the modbus packet to interact with the inverter.
        """
        # Compute CRC of modbus content
        crc = computeCRC(content)

        # Assemble the modbus content into the mqtt packet framework
        req_id = int(random() * 65536)
        rand = int(random() * 65536)
        packet = pack(">HBBH", req_id, 0x58, 0xC9, rand) + content + pack(">H", crc)

        debug(f"Request id: {log_hex(req_id)}", self._debug)
        debug(f"Request type: {log_hex(req_type)}", self._debug)
        debug(f"CRC: {log_hex(crc)}", self._debug)
        debug(f"Request length: {len(packet)} bytes", self._debug)
        debug(f"Request bytes: {':'.join(f'{b:02x}' for b in packet)}", self._debug)

        packet = pack(">H", len(packet)) + packet

        debug(f"Final packet: {':'.join(f'{b:02x}' for b in packet)}", self._debug)

        return packet, req_id


class SajH1ModbusClient(SajH1Client):
    """SAJ H1 modbus client."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        delay: float = 0,
        wait: float = 0,
        modbus_debug: bool = False,
    ) -> None:
        """Set up the SajH1ModbusClient class."""
        super().__init__(hass)

        self.host = host
        self.port = port
        self._delay = delay
        self._wait = wait
        self._debug = modbus_debug
        self._client = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to modbus."""
        self._client = AsyncModbusTcpClient(
            host=self.host, port=self.port, timeout=MODBUS_TIMEOUT
        )
        try:
            if await self._client.connect():
                debug(f"Connected to modbus at {self.host}:{self.port}")
                # Small delay after connecting
                if self._delay:
                    await asyncio.sleep(self._delay)
            else:
                self._client = None
                raise ConnectionError(
                    f"Failed to connect to modbus at {self.host}:{self.port}"
                )
        except ModbusException as ex:
            self._client = None
            raise ConnectionError(
                f"Failed to connect to modbus at {self.host}:{self.port}"
            ) from ex

    async def disconnect(self) -> None:
        """Disconnect from modbus."""
        if self._client:
            try:
                self._client.close()
                debug(f"Disconnected from modbus at {self.host}:{self.port}")
            except ModbusException as ex:
                LOGGER.error(f"Failed to disconnect from modbus: {ex}")
            self._client = None

    async def read_registers(
        self,
        register_start: int,
        register_count: int,
        register_chunks: list[int] | None = None,
    ) -> bytearray | None:
        """Read 1 or more registers from the inverter.

        We can read up to 125 registers with a single request.
        Because a modbus tcp response cannot exceed 260 bytes. (125 registers = 250 bytes, plus some overhead)
        This method hides all the package splitting and returns the raw bytes if successful.
        You can also specify the register_chunks, so you can group the registers that belong together.
        It returns None in case data could not be retrieved.
        """
        async with self._lock:
            debug(
                f"Reading registers at {log_hex(register_start)}, length: {log_hex(register_count)}"
            )

            data = bytearray()
            chunk_idx = 0
            while register_count > 0:
                if register_chunks:
                    # If register_chunks are provided, we need to split the requests according to the chunks
                    reg_count = register_chunks[chunk_idx]
                else:
                    # If no register_chunks are provided, split in chunks of max MODBUS_MAX_REGISTERS registers
                    reg_count = min(register_count, MODBUS_MAX_REGISTERS)
                chunk_idx += 1

                # Read the registers, with retries in case of modbus errors
                debug(
                    f"Reading register chunk {chunk_idx} at {log_hex(register_start)}, length: {log_hex(reg_count)}"
                )
                for attempt in range(MODBUS_RETRY_COUNT):
                    try:
                        response = await self._client.read_holding_registers(
                            address=register_start,
                            count=reg_count,
                            device_id=MODBUS_DEVICE_ADDRESS,
                        )
                        debug(f"Modbus response: {response}", self._debug)
                        if not response.isError():
                            break

                        debug(
                            f"Modbus error: {response.exception_code}, attempt {attempt + 1}/{MODBUS_RETRY_COUNT}",
                            self._debug,
                        )

                    except ModbusException as ex:
                        debug(
                            f"Modbus exception: {ex}, attempt {attempt + 1}/{MODBUS_RETRY_COUNT}",
                            self._debug,
                        )

                    await asyncio.sleep(MODBUS_RETRY_DELAY)
                else:
                    LOGGER.error(
                        f"Failed to read registers at {log_hex(register_start)}, length: {log_hex(reg_count)}"
                    )
                    data = None
                    break  # in case of failure, break the while loop and return None

                # Register chunk read, append the values to the data bytearray
                for value in response.registers:
                    data.extend(value.to_bytes(2, byteorder="big"))

                # Update the register_start and register_count for the next chunk
                register_start += reg_count
                register_count -= reg_count

            # Small wait until next request/response
            if self._wait:
                await asyncio.sleep(self._wait)

            return data

    async def write_register(self, register: int, value: int) -> int | None:
        """Write a register value to the inverter."""
        async with self._lock:
            debug(f"Writing register at {log_hex(register)}, value: {log_hex(value)}")

            data: int | None = None
            try:
                response = await self._client.write_register(
                    address=register, value=value, device_id=MODBUS_DEVICE_ADDRESS
                )
                debug(f"Modbus response: {response}", self._debug)
                if response.isError():
                    LOGGER.error(
                        f"Failed to write register at {log_hex(register)}: modbus error {response.exception_code}"
                    )
                    data = None
                else:
                    data = response.registers[0]  # the value written to the register

            except ModbusException as ex:
                LOGGER.error(f"Modbus exception: {ex}")
                data = None

            # Small delay until next request/response
            if self._wait:
                await asyncio.sleep(self._wait)

            return data

    async def write_registers(
        self, register_start: int, values: list[int]
    ) -> int | None:
        """Write multiple register values to the inverter."""
        async with self._lock:
            count = len(values)
            hex_values = ", ".join(log_hex(v) for v in values)
            debug(
                f"Writing register(s) at {log_hex(register_start)}, length: {log_hex(count)}, values: {hex_values}"
            )

            data: int | None = None
            try:
                response = await self._client.write_registers(
                    address=register_start,
                    values=values,
                    device_id=MODBUS_DEVICE_ADDRESS,
                )
                debug(f"Modbus response: {response}", self._debug)
                if response.isError():
                    LOGGER.error(
                        f"Failed to write registers at {log_hex(register_start)}: modbus error {response.exception_code}"
                    )
                    data = None
                else:
                    data = response.count  # number of registers written

            except ModbusException as ex:
                LOGGER.error(f"Modbus exception: {ex}")
                data = None

            # Small delay until next request/response
            if self._wait:
                await asyncio.sleep(self._wait)

            return data
