from __future__ import annotations

import asyncio
import logging
from typing import Union
from uuid import UUID

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from . import characteristics
from . import helpers as h
from .parser import SkyModeParser
from .sensors import SkySensors


class FreshIntelliVent:
    def __init__(self, ble_device: BLEDevice) -> None:
        self.parser = SkyModeParser()

        self.address = ble_device.address
        self._ble_device = ble_device
        self.sensors = SkySensors()
        self.modes = {}

        self._client: BleakClient | None = None

        self.hw_version = None
        self.sw_version = None

        self.name = None
        self.manufacturer = None
        self.model = "Intellivent Sky"
        self.fw_version = None
        self.hw_version = None
        self.sw_version = None

    async def connect(self, timeout: float = 30.0):
        self._client = await establish_connection(
            BleakClient, self._ble_device, self._ble_device.address
        )
        self._connected = True

        logging.debug("Connected to {ble_device.address}")

    async def disconnect(self):
        if self._client is None:
            logging.debug("Already disconnected")
        else:
            await self._client.disconnect()
            logging.debug("Disconnected")
        self._client = None
        self._connected = False

    async def authenticate(self, authentication_code: Union[bytes, bytearray, str]):
        logging.debug("Authenticating...")

        await self._write_characteristic(
            uuid=characteristics.AUTH, data=h.to_bytearray(authentication_code)
        )

        await asyncio.sleep(1)

        logging.debug("Authenticated!")

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
            logging.info(f"MSG: {h.to_hex(data)} ({len(data)})")
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
        logging.info(f"[{command}] {uuid} = {h.to_hex(bytes)}")

    async def fetch_device_information(self):
        logging.debug("Fetching device information")

        name = await self._client.read_gatt_char(
            char_specifier=characteristics.DEVICE_NAME
        )
        self.name = name.decode("utf-8").replace("\00", "").replace("\0", "")

        fw_version = await self._client.read_gatt_char(
            char_specifier=characteristics.FIRMWARE_VERSION
        )
        self.fw_version = fw_version.decode("utf-8")

        hw_version = await self._client.read_gatt_char(
            char_specifier=characteristics.HARDWARE_VERSION
        )
        self.hw_version = hw_version.decode("utf-8")

        hw_version = await self._client.read_gatt_char(
            char_specifier=characteristics.SOFTWARE_VERSION
        )
        self.hw_version = hw_version.decode("utf-8")

        manufacturer = await self._client.read_gatt_char(
            char_specifier=characteristics.MANUFACTURER_NAME
        )
        self.manufacturer = manufacturer.decode("utf-8")

        logging.debug(
            "Device fetched! Manufacturer: {}, name: {}, FW: {}, HW: {}".format(
                self.manufacturer, self.name, self.fw_version, self.hw_version
            )
        )

    async def fetch_humidity(self):
        value = await self._read_characterisitc(uuid=characteristics.HUMIDITY)
        humidity = self.parser.humidity_read(value=value)
        self.modes["humidity"] = humidity
        return humidity

    async def update_humidity(self, enabled: bool, detection: str, rpm: int):
        value = self.parser.humidity_write(
            enabled=enabled, detection=detection, rpm=rpm
        )
        await self._write_characteristic(characteristics.HUMIDITY, value)
        self.modes["humidity"] = {
            "enabled": enabled,
            "detection": detection,
            "detection_raw": h.detection_string_as_int(detection),
            "rpm": rpm,
        }

    async def fetch_light_and_voc(self):
        value = await self._read_characterisitc(uuid=characteristics.LIGHT_VOC)
        light_and_voc = self.parser.light_and_voc_read(value=value)
        self.modes["light_and_voc"] = light_and_voc
        return light_and_voc

    async def update_light_and_voc(
        self,
        light_enabled: bool,
        light_detection: str,
        voc_enabled: bool,
        voc_detection: str,
    ):
        value = self.parser.light_and_voc_write(
            light_enabled=light_enabled,
            light_detection=light_detection,
            voc_enabled=voc_enabled,
            voc_detection=voc_detection,
        )
        await self._write_characteristic(characteristics.LIGHT_VOC, value)
        self.modes["light_and_voc"] = {
            "light": {
                "enabled": light_enabled,
                "detection": light_detection,
                "detection_raw": h.detection_string_as_int(light_detection),
            },
            "voc": {
                "enabled": voc_enabled,
                "detection": voc_detection,
                "detection_raw": h.detection_string_as_int(voc_detection),
            },
        }

    async def fetch_constant_speed(self):
        value = await self._read_characterisitc(uuid=characteristics.CONSTANT_SPEED)
        constant_speed = self.parser.constant_speed_read(value=value)
        self.modes["constant_speed"] = constant_speed
        return constant_speed

    async def update_constant_speed(self, enabled: bool, rpm: int):
        value = self.parser.constant_speed_write(enabled=enabled, rpm=rpm)
        hex = h.to_hex(value)
        await self._write_characteristic(
            characteristics.CONSTANT_SPEED, bytearray.fromhex(hex)
        )
        self.modes["constant_speed"] = {"enabled": enabled, "rpm": rpm}

    async def fetch_timer(self):
        value = await self._read_characterisitc(uuid=characteristics.TIMER)
        timer = self.parser.timer_read(value=value)
        self.modes["timer"] = timer
        return timer

    async def update_timer(
        self, minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int
    ):
        value = self.parser.timer_write(
            minutes=minutes,
            delay_enabled=delay_enabled,
            delay_minutes=delay_minutes,
            rpm=rpm,
        )
        await self._write_characteristic(characteristics.TIMER, value)
        self.modes["timer"] = {
            "delay": {"enabled": delay_enabled, "minutes": delay_minutes},
            "minutes": minutes,
            "rpm": rpm,
        }

    async def fetch_airing(self):
        value = await self._read_characterisitc(uuid=characteristics.AIRING)
        airing = self.parser.airing_read(value=value)
        self.modes["airing"] = airing
        return airing

    async def update_airing(self, enabled: bool, minutes: int, rpm: int):
        value = self.parser.airing_write(enabled=enabled, minutes=minutes, rpm=rpm)
        await self._write_characteristic(characteristics.AIRING, value)
        self.modes["airing"] = {
            "enabled": enabled,
            "minutes": minutes,
            "rpm": rpm,
        }

    async def fetch_pause(self):
        value = await self._read_characterisitc(uuid=characteristics.PAUSE)
        return self.parser.pause_read(value=value)

    async def update_pause(self, enabled: bool, minutes: int):
        value = self.parser.pause_write(enabled=enabled, minutes=minutes)
        await self._write_characteristic(characteristics.PAUSE, value)
        self.modes["pause"] = {"enabled": enabled, "minutes": minutes}

    async def fetch_boost(self):
        value = await self._read_characterisitc(uuid=characteristics.BOOST)
        return self.parser.boost_read(value=value)

    async def update_boost(self, enabled: bool, rpm: int, seconds: int):
        value = self.parser.boost_write(enabled=enabled, rpm=rpm, seconds=seconds)
        await self._write_characteristic(characteristics.BOOST, value)
        self.modes["boost"] = {"enabled": enabled, "seconds": seconds, "rpm": rpm}

    async def update_temporary_speed(self, enabled: bool, rpm: int):
        value = self.parser.temporary_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.TEMPORARY_SPEED, value)

    async def fetch_sensor_data(self):
        data = await self._read_characterisitc(uuid=characteristics.DEVICE_STATUS)
        self.sensors.parse_data(data)
        return self.sensors


class FreshIntelliventError(Exception):
    pass


class FreshIntelliventTimeoutError(FreshIntelliventError):
    pass
