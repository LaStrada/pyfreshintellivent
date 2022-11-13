from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from struct import pack, unpack
from typing import AsyncIterator, Union
from uuid import UUID

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from . import characteristics
from . import helpers as h


class FreshIntelliventError(Exception):
    pass


class FreshIntelliventTimeoutError(FreshIntelliventError):
    pass


class FreshIntelliventAuthenticationError(FreshIntelliventError):
    pass


class FreshIntelliVent:
    def __init__(
        self, address_or_ble_device: Union[BLEDevice, str, None] = None
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.parser = SkyModeParser()
        self.address_or_ble_device = address_or_ble_device

        self._lock = asyncio.Lock()
        self._client: BleakClient | None = None
        self._client_stack = AsyncExitStack()
        self._client_count = 0

    @asynccontextmanager
    async def connect(
        self,
        address_or_ble_device: Union[BLEDevice, str, None] = None,
        timeout: float = 20.0,
    ) -> AsyncIterator[FreshIntelliVent]:
        if address_or_ble_device is not None:
            self.address_or_ble_device = address_or_ble_device

        async with self._lock:
            if not self._client:
                try:
                    self.logger.debug(f"Searching for {self.address_or_ble_device}")
                    self._client = await self._client_stack.enter_async_context(
                        BleakClient(self.address_or_ble_device, timeout=timeout)
                    )
                except asyncio.TimeoutError as exc:
                    logging.info("Timeout on connect", exc_info=exc)
                    raise FreshIntelliventTimeoutError("Timeout on connect") from exc
                except BleakError as exc:
                    logging.info("Error on connect", exc_info=exc)
                    raise FreshIntelliventError("Error on connect") from exc
            else:
                logging.info("Connection reused")
            self._client_count += 1

        try:
            async with self._lock:
                yield self
        finally:
            async with self._lock:
                self._client_count -= 1
                if self._client_count == 0:
                    self._client = None
                    logging.info("Disconnected")
                    await self._client_stack.pop_all().aclose()

    async def authenticate(self, authentication_code: Union[bytes, bytearray, str]):
        self.logger.info("Authenticating...")
        await self._write_characteristic(
            uuid=characteristics.AUTH, data=h.to_bytearray(authentication_code)
        )
        await asyncio.sleep(2)  # Make sure we're authenticated
        self.logger.info("Authenticated!")

    async def fetch_authentication_code(self):
        code = await self._client.read_gatt_char(char_specifier=characteristics.AUTH)
        return code

    async def _read_characterisitc(self, uuid: Union[str, UUID]):
        if self._client is None:
            raise FreshIntelliventError("Not connected")

        try:
            value = await self._client.read_gatt_char(char_specifier=uuid)
            self._log_data(command="R", uuid=uuid, bytes=value)
            return value
        except asyncio.TimeoutError as exc:
            logging.info(f"Timeout on read: {uuid}")
            raise TimeoutError("Timeout on read") from exc
        except BleakError as exc:
            logging.info(f"Failed to read: {uuid}")
            raise FreshIntelliventError("Failed to read") from exc

    async def _write_characteristic(
        self, uuid: Union[str, UUID], data: Union[bytes, bytearray]
    ):
        if self._client is None:
            raise FreshIntelliventError("Not connected")

        try:
            self._log_data(command="W", uuid=uuid, bytes=data)
            self.logger.info(f"MSG: {h.to_hex(data)} ({len(data)})")
            await self._client.write_gatt_char(
                char_specifier=uuid, data=data, response=True
            )
        except asyncio.TimeoutError as exc:
            logging.info(f"Timeout on write: {uuid}")
            raise TimeoutError("Timeout on write") from exc
        except BleakError as exc:
            logging.info(f"Failed to write: {uuid}")
            raise FreshIntelliventError("Failed to write") from exc

    def _log_data(self, command: str, uuid: str, bytes: Union[bytes, bytearray]):
        self.logger.info(f"[{command}] {uuid} = {h.to_hex(bytes)}")

    async def get_humidity(self):
        value = await self._read_characterisitc(uuid=characteristics.HUMIDITY)
        return self.parser.humidity_read(value=value)

    async def set_humidity(self, enabled: bool, detection: int, rpm: int):
        value = self.parser.humidity_write(
            enabled=enabled, detection=detection, rpm=rpm
        )
        await self._write_characteristic(characteristics.HUMIDITY, value)

    async def get_light_and_voc(self):
        value = await self._read_characterisitc(uuid=characteristics.LIGHT_VOC)
        return self.parser.light_and_voc_read(value=value)

    async def set_light_and_voc(
        self,
        light_enabled: bool,
        light_detection: int,
        voc_enabled: bool,
        voc_detection: int,
    ):
        value = self.parser.light_and_voc_write(
            light_enabled=light_enabled,
            light_detection=light_detection,
            voc_enabled=voc_enabled,
            voc_detection=voc_detection,
        )
        await self._write_characteristic(characteristics.LIGHT_VOC, value)

    async def get_constant_speed(self):
        value = await self._read_characterisitc(uuid=characteristics.CONSTANT_SPEED)
        return self.parser.constant_speed_read(value=value)

    async def set_constant_speed(self, enabled: bool, rpm: int):
        value = self.parser.constant_speed_write(enabled=enabled, rpm=rpm)
        hex = h.to_hex(value)
        await self._write_characteristic(
            characteristics.CONSTANT_SPEED, bytearray.fromhex(hex)
        )

    async def get_timer(self):
        value = await self._read_characterisitc(uuid=characteristics.TIMER)
        return self.parser.timer_read(value=value)

    async def set_timer(
        self, minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int
    ):
        value = self.parser.timer_write(
            minutes=minutes,
            delay_enabled=delay_enabled,
            delay_minutes=delay_minutes,
            rpm=rpm,
        )
        await self._write_characteristic(characteristics.TIMER, value)

    async def get_airing(self):
        value = await self._read_characterisitc(uuid=characteristics.AIRING)
        return self.parser.airing_read(value=value)

    async def set_airing(self, enabled: bool, minutes: int, rpm: int):
        value = self.parser.airing_write(enabled=enabled, minutes=minutes, rpm=rpm)
        await self._write_characteristic(characteristics.AIRING, value)

    async def get_pause(self):
        value = await self._read_characterisitc(uuid=characteristics.PAUSE)
        return self.parser.pause_read(value=value)

    async def set_pause(self, enabled: bool, minutes: int):
        value = self.parser.pause_write(enabled=enabled, minutes=minutes)
        await self._write_characteristic(characteristics.PAUSE, value)

    async def get_boost(self):
        value = await self._read_characterisitc(uuid=characteristics.BOOST)
        return self.parser.boost_read(value=value)

    async def set_boost(self, enabled: bool, rpm: int, seconds: int):
        value = self.parser.boost_write(enabled=enabled, rpm=rpm, seconds=seconds)
        await self._write_characteristic(characteristics.BOOST, value)

    async def set_temporary_speed(self, enabled: bool, rpm: int):
        value = self.parser.temporary_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.TEMPORARY_SPEED, value)

    async def get_sensor_data(self):
        data = await self._read_characterisitc(uuid=characteristics.DEVICE_STATUS)
        return SkySensors(data)


class SkySensors(object):
    def __init__(self, data: Union[bytes, bytearray]):
        if data is None or len(data) != 15:
            raise ValueError(f"Length need to be exactly 15, was {len(data)}.")

        values = unpack("<2B2H2B2H3B", data)

        self._values = values

        self.status = bool(values[0])
        self.mode = values[1]

        self.humidity = values[2] / 10
        self.temperature_1 = values[3] / 100
        self.temperature_2 = values[7] / 100
        self.unknowns = [values[4], values[8], values[9], values[10]]
        self.authenticated = bool(values[5])

        self.rpm = values[6]

        if self.mode == 0:
            self.mode_description = "Off"
        elif self.mode == 6:
            self.mode_description = "Pause"
        elif self.mode == 16:
            self.mode_description = "Constant speed"
        elif self.mode == 34:
            self.mode_description = "Light"
        elif self.mode == 49:
            self.mode_description = "Humidity"
        elif self.mode == 52:
            self.mode_description = "VOC"
        elif self.mode == 103:
            self.mode_description = "Boost"
        else:
            self.mode_description = "Unknown"

    def as_dict(self):
        return {
            "status": self.status,
            "mode": {
                "description": self.mode_description,
                "raw_value": self.mode,
            },
            "temperatures": [self.temperature_1, self.temperature_2],
            "rpm": self.rpm,
            "humidity": self.humidity,
            "unknowns": self.unknowns,
            "authenticated": self.authenticated,
        }


class SkyModeParser(object):
    def airing_read(self, value: Union[bytes, bytearray]):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<?2BH", value)

        enabled = bool(value[0])
        minutes = h.validated_time(int(value[2]))
        rpm = int(value[3])

        return {
            "enabled": enabled,
            "minutes": minutes,
            "rpm": rpm,
        }

    def airing_write(self, enabled: bool, minutes: int, rpm: int):
        return pack(
            "<?2BH", enabled, 26, h.validated_time(minutes), h.validated_rpm(rpm)
        )

    def boost_read(self, value: Union[bytes, bytearray]):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")
        value = unpack("<?2H", value)

        enabled = bool(value[0])
        rpm = int(value[1])
        seconds = int(value[2])

        return {"enabled": enabled, "seconds": seconds, "rpm": rpm}

    def boost_write(self, enabled: bool, rpm: int, seconds: int):
        val = pack("<?2H", enabled, h.validated_rpm(rpm), h.validated_time(seconds))
        return val

    def constant_speed_read(self, value: Union[bytes, bytearray]):
        if len(value) != 3:
            raise ValueError(f"Length need to be exactly 3, was {len(value)}.")
        value = unpack("<?H", value)

        enabled = bool(value[0])
        rpm = int(value[1])

        return {"enabled": enabled, "rpm": rpm}

    def constant_speed_write(self, enabled: bool, rpm: int):
        return pack("<?H", enabled, h.validated_rpm(rpm))

    def humidity_read(self, value: Union[bytes, bytearray]):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<?BH", value)

        enabled = bool(value[0])
        detection = int(value[1])
        rpm = int(value[2])

        return {
            "enabled": enabled,
            "detection": detection,
            "detection_description": self.detection_as_string(detection),
            "rpm": rpm,
        }

    def humidity_write(self, enabled: bool, detection: int, rpm: int):
        return pack(
            "<?BH", enabled, h.validated_detection(detection), h.validated_rpm(rpm)
        )

    def light_and_voc_read(self, value: Union[bytes, bytearray]):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<?B?B", value)

        light_enabled = bool(value[0])
        light_detection = int(value[1])
        voc_enabled = bool(value[2])
        voc_detection = int(value[3])

        return {
            "light": {
                "enabled": light_enabled,
                "detection": light_detection,
                "detection_description": self.detection_as_string(
                    light_detection, False
                ),
            },
            "voc": {
                "enabled": voc_enabled,
                "detection": voc_detection,
                "detection_description": self.detection_as_string(voc_detection),
            },
        }

    def light_and_voc_write(
        self,
        light_enabled: bool,
        light_detection: int,
        voc_enabled: bool,
        voc_detection: int,
    ):
        return pack(
            "<?B?B",
            bool(light_enabled),
            h.validated_detection(light_detection),
            bool(voc_enabled),
            h.validated_detection(voc_detection),
        )

    def pause_read(self, value: Union[bytes, bytearray]):
        if len(value) != 2:
            raise ValueError(f"Length need to be exactly 2, was {len(value)}.")

        value = unpack("<?B", value)

        enabled = bool(value[0])
        minutes = int(value[1])

        return {"enabled": enabled, "minutes": minutes}

    def pause_write(self, enabled: bool, minutes: int):
        return pack("<?B", enabled, h.validated_time(minutes))

    def temporary_speed_write(self, enabled: bool, rpm: int):
        return pack("<?H", enabled, h.validated_rpm(rpm))

    def timer_read(self, value: Union[bytes, bytearray]):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<B?BH", value)

        minutes = int(value[0])
        delay_enabled = bool(value[1])
        delay_minutes = int(value[2])
        rpm = int(value[3])

        return {
            "delay": {"enabled": delay_enabled, "minutes": delay_minutes},
            "minutes": minutes,
            "rpm": rpm,
        }

    def timer_write(
        self, minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int
    ):
        return pack(
            "<B?BH",
            minutes,
            delay_enabled,
            delay_minutes,
            h.validated_rpm(rpm),
        )

    def detection_as_string(self, value: int, regular_order: bool = True):
        value = h.validated_detection(value)
        if value == 1:
            return "Low" if regular_order else "High"
        elif value == 2:
            return "Medium"
        elif value == 3:
            return "High" if regular_order else "Low"
        else:
            return "Unknown"
