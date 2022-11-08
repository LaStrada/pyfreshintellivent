from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from . import characteristics
from . import helpers as h
from . import skyModeParser as parser
from skySensors import SkySensors
from struct import pack, unpack


class Sky(object):
    client = None

    def __init__(self, debug=False):
        self._debug = debug

    async def disconnect(self):
        try:
            if self.client.is_connected:
                await self.client.disconnect()
                self._log_message("Info", "Disconnected.")
            else:
                self._log_message("Info", "Already disconnected.")
        except AttributeError:
            self._log_message("Info", "No clients available.")
        finally:
            self.client = None

    async def connect_and_authenticate(
        self, ble_address, authentication_code, timeout=5.0
    ):
        h.validate_authentication_code(authentication_code)

        device = await BleakScanner.find_device_by_address(
            device_identifier=ble_address, timeout=timeout
        )
        if not device:
            raise BleakError(
                f"A device with address {ble_address} " "could not be found."
            )
        self._log_message("Info", f"Found {ble_address}")

        self.client = BleakClient(device)

        await self.client.connect()
        self._log_message("Info", f"Connected to {ble_address}")

        await self._authenticate(authentication_code)

    async def _authenticate(self, authentication_code):
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH, data=bytes.fromhex(authentication_code)
        )
        self._log_message("Info", "Authenticated.")

    async def fetch_authentication_code(self, device: BleakClient):
        code = await device.read_gatt_char(char_specifier=characteristics.AUTH)
        return code

    async def _read_characterisitc(self, uuid):
        value = await self.client.read_gatt_char(char_specifier=uuid)
        self._log_data(command="R", uuid=uuid, message=value)
        return value

    async def _write_characteristic(self, uuid, value):
        self._log_data(command="W", uuid=uuid, message=value)
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH, data=bytes.fromhex(value)
        )

    def _log_message(self, level, message):
        if self._debug:
            print(f"[Fresh Intellivent Sky] [{level}] {message}")

    def _log_data(self, command, uuid, message):
        hex = "".join("{:02x}".format(x) for x in message)
        self._log_message(
            level=command, message=f"[{command}] {uuid} = {hex or message}"
        )

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
        self, light_enabled, light_detection, voc_enabled, voc_detection
    ):
        await self._write_characteristic(characteristics.LIGHT_VOC, value)

    async def get_constant_speed(self):
        value = await self._read_characterisitc(uuid=characteristics.CONSTANT_SPEED)
        parser.constant_speed_read(value=value)

    async def set_constant_speed(self, constant_speed_enabled, constant_speed_rpm):
        value = pack("<BH", constant_speed_enabled, h.validatedRPM(constant_speed_rpm))

        await self._write_characteristic(characteristics.CONSTANT_SPEED, value)

    async def get_timer(self):
        value = await self._read_characterisitc(uuid=characteristics.TIMER)
        return parser.timer(value=value)

    async def set_timer(self, running_time, delay_enabled, delay_minutes, rpm):
        value = pack(
            "<3BH",
            running_time,
            bool(delay_enabled),
            delay_minutes,
            h.validated_rpm(rpm),
        )

        await self._write_characteristic(characteristics.TIMER, value)

    async def get_airing(self):
        value = await self._read_characterisitc(uuid=characteristics.AIRING)
        return parser.airing_mode_read(value=value)

    async def set_airing(self, enabled: bool, minutes: int, rpm: int):
        value = parser.airing_mode_write(
            enabled=enabled,
            run_time=minutes,
            rpm=rpm
        )
        await self._write_characteristic(characteristics.AIRING, value)

    async def get_pause(self):
        value = await self._read_characterisitc(uuid=characteristics.PAUSE)
        parser.pause(value=value)

    async def set_pause(self, enabled: bool, minutes: int):
        value = parser.pause_write(enabled=enabled, minutes=minutes)
        await self._write_characteristic(characteristics.PAUSE, value)

    async def get_boost(self):
        value = await self._read_characterisitc(uuid=characteristics.BOOST)
        return parser.boost(value=value)

    async def set_boost(self, boost_enabled, boost_minutes, boost_rpm):
        await self._write_characteristic(characteristics.BOOST, value)

    async def set_temporary_speed(self, enabled: bool, rpm: int):
        value = parser.temporary_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.TEMPORARY_SPEED, value)

    async def get_sensor_data(self):
        data = unpack(
            "<2B5HBH",
            await self._read_characterisitc(uuid=characteristics.DEVICE_STATUS),
        )
        return SkySensors(data)
