from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator, Union
from uuid import UUID

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from . import characteristics
from . import helpers as h
from .sensors import SkySensors
from .skyModeParser import SkyModeParser


DEVICE_NAME = "Intellivent SKY"
UUID_SERVICE = UUID("{0000180a-0000-1000-8000-00805f9b34fb}")


class FreshIntelliVent:
    def __init__(
        self, address: str
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.parser = SkyModeParser()
        self.address = address

        self.state = SkySensors()

        self._lock = asyncio.Lock()
        self._client: BleakClient | None = None
        self._client_stack = AsyncExitStack()
        self._client_count = 0

    @asynccontextmanager
    async def connect(
        self,
        timeout: float = 20.0,
    ) -> AsyncIterator[FreshIntelliVent]:
        async with self._lock:
            if not self._client:
                try:
                    self.logger.debug(f"Searching for {self.address}")
                    self._client = await self._client_stack.enter_async_context(
                        BleakClient(self.address, timeout=timeout)
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

    async def set_humidity(self, enabled: bool, detection: Union[int, str], rpm: int):
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
        self.state.parse_data(data)
        return state
    
    def detection_callback(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """Handle scanner data."""
        return


def device_filter(device: BLEDevice, advertisement_data: AdvertisementData) -> bool:
    uuids = advertisement_data.service_uuids
    if str(UUID_SERVICE) in uuids:
        return True

    if device.name == DEVICE_NAME:
        return True

    return False


class FreshIntelliventError(Exception):
    pass


class FreshIntelliventTimeoutError(FreshIntelliventError):
    pass


class FreshIntelliventAuthenticationError(FreshIntelliventError):
    pass
