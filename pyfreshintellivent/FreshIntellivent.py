from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
import logging
from . import characteristics
from . import helpers as h
from . import skyModeParser as parser
from .skySensors import SkySensors


class Sky(object):
    client = None
    logger = logging.getLogger(__name__)

    async def disconnect(self):
        try:
            if self.client.is_connected:
                await self.client.disconnect()
            self.logger.info("Disconnected.")
        except AttributeError:
            self.logger.info("No clients available.")
        finally:
            self.client = None

    async def connect_and_authenticate(
        self, ble_address: str, authentication_code: str, timeout: float = 5.0
    ):
        h.validate_authentication_code(authentication_code)

        device = await BleakScanner.find_device_by_address(
            device_identifier=ble_address, timeout=timeout
        )
        if not device:
            raise BleakError(
                f"A device with address {ble_address} " "could not be found."
            )
        self.logger.info(f"Found {ble_address}")

        self.client = BleakClient(device)

        await self.client.connect()
        self.logger.info(f"Connected to {ble_address}")

        await self._authenticate(authentication_code)

    async def _authenticate(self, authentication_code: str):
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH, data=bytes.fromhex(authentication_code)
        )
        self.logger.info("Authenticated")

    async def fetch_authentication_code(self, device: BleakClient):
        code = await device.read_gatt_char(char_specifier=characteristics.AUTH)
        return code

    async def _read_characterisitc(self, uuid: str):
        value = await self.client.read_gatt_char(char_specifier=uuid)
        self._log_data(command="R", uuid=uuid, message=value)
        return value

    async def _write_characteristic(self, uuid: str, value):
        # TODO: Value type??
        self._log_data(command="W", uuid=uuid, message=value)
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH, data=bytes.fromhex(value)
        )

    def _log_data(self, command, uuid, message):
        hex = "".join("{:02x}".format(x) for x in message)
        self.logger.info(f"[{command}] {uuid} = {hex or message}")

    async def get_humidity(self):
        value = await self._read_characterisitc(uuid=characteristics.HUMIDITY)
        return parser.humidity_mode(value=value)

    async def set_humidity(self, enabled: bool, detection: int, rpm: int):
        value = parser.humidity_mode_write(enable=enabled, detection=detection, rpm=rpm)
        await self._write_characteristic(characteristics.HUMIDITY, value)

    async def get_light_and_voc(self):
        value = await self._read_characterisitc(uuid=characteristics.LIGHT_VOC)
        return parser.light_and_voc(value=value)

    async def set_light_voc(
        self,
        light_enabled: bool,
        light_detection: int,
        voc_enabled: bool,
        voc_detection: int,
    ):
        value = parser.light_and_voc_write(
            light_enabled=light_enabled,
            light_detection=light_detection,
            voc_enabled=voc_enabled,
            voc_detection=voc_detection,
        )
        await self._write_characteristic(characteristics.LIGHT_VOC, value)

    async def get_constant_speed(self):
        value = await self._read_characterisitc(uuid=characteristics.CONSTANT_SPEED)
        return parser.constant_speed_read(value=value)

    async def set_constant_speed(self, enabled, rpm):
        value = parser.constant_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.CONSTANT_SPEED, value)

    async def get_timer(self):
        value = await self._read_characterisitc(uuid=characteristics.TIMER)
        return parser.timer_read(value=value)

    async def set_timer(
        self, minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int
    ):
        value = parser.timer_write(
            minutes=minutes,
            delay_enabled=delay_enabled,
            delay_minutes=delay_minutes,
            rpm=rpm,
        )
        await self._write_characteristic(characteristics.TIMER, value)

    async def get_airing(self):
        value = await self._read_characterisitc(uuid=characteristics.AIRING)
        return parser.airing_mode_read(value=value)

    async def set_airing(self, enabled: bool, minutes: int, rpm: int):
        value = parser.airing_mode_write(enabled=enabled, run_time=minutes, rpm=rpm)
        await self._write_characteristic(characteristics.AIRING, value)

    async def get_pause(self):
        value = await self._read_characterisitc(uuid=characteristics.PAUSE)
        return parser.pause(value=value)

    async def set_pause(self, enabled: bool, minutes: int):
        value = parser.pause_write(enabled=enabled, minutes=minutes)
        await self._write_characteristic(characteristics.PAUSE, value)

    async def get_boost(self):
        value = await self._read_characterisitc(uuid=characteristics.BOOST)
        return parser.boost_read(value=value)

    async def set_boost(self, enabled: bool, minutes: int, rpm: int):
        value = parser.boost_write(enabled=enabled, minutes=minutes, rpm=rpm)
        await self._write_characteristic(characteristics.BOOST, value)

    async def set_temporary_speed(self, enabled: bool, rpm: int):
        value = parser.temporary_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.TEMPORARY_SPEED, value)

    async def get_sensor_data(self):
        data = await self._read_characterisitc(uuid=characteristics.DEVICE_STATUS)
        return SkySensors(data)
