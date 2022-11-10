import logging
from struct import pack, unpack

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

from . import characteristics
from . import helpers as h


class FreshIntelliVent(object):
    def __init__(self) -> None:
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.parser = SkyModeParser()

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
        self._log_data(command="W", uuid=uuid, message=value)
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH, data=bytes.fromhex(value)
        )

    def _log_data(self, command, uuid, message):
        hex = "".join("{:02x}".format(x) for x in message)
        self.logger.info(f"[{command}] {uuid} = {hex or message}")

    async def get_humidity(self):
        value = await self._read_characterisitc(uuid=characteristics.HUMIDITY)
        return self.parser.humidity_mode_read(value=value)

    async def set_humidity(self, enabled: bool, detection: int, rpm: int):
        value = self.parser.humidity_mode_write(
            enable=enabled, detection=detection, rpm=rpm
        )
        await self._write_characteristic(characteristics.HUMIDITY, value)

    async def get_light_and_voc(self):
        value = await self._read_characterisitc(uuid=characteristics.LIGHT_VOC)
        return self.parser.light_and_voc_read(value=value)

    async def set_light_voc(
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

    async def set_constant_speed(self, enabled, rpm):
        value = self.parser.constant_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.CONSTANT_SPEED, value)

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
        return self.parser.airing_mode_read(value=value)

    async def set_airing(self, enabled: bool, minutes: int, rpm: int):
        value = self.parser.airing_mode_write(
            enabled=enabled, run_time=minutes, rpm=rpm
        )
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

    async def set_boost(self, enabled: bool, minutes: int, rpm: int):
        value = self.parser.boost_write(enabled=enabled, minutes=minutes, rpm=rpm)
        await self._write_characteristic(characteristics.BOOST, value)

    async def set_temporary_speed(self, enabled: bool, rpm: int):
        value = self.parser.temporary_speed_write(enabled=enabled, rpm=rpm)
        await self._write_characteristic(characteristics.TEMPORARY_SPEED, value)

    async def get_sensor_data(self):
        data = await self._read_characterisitc(uuid=characteristics.DEVICE_STATUS)
        return SkySensors(data)


class SkySensors(object):
    def __init__(self, data: bytearray):
        if data is None or len(data) != 15:
            raise ValueError(f"Length of object need to be 15, was {len(data)}.")

        values = unpack("<2B5HBH", data)

        self._values = values

        self.status = bool(values[0])
        self.mode = values[1]
        self.rpm = values[5]
        self.mode_description = "Unknown"

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
            "rpm": self.rpm,
        }


class SkyModeParser(object):
    def airing_mode_read(value):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<3BH", value)

        enabled = bool(value[0])
        minutes = int(value[2])
        rpm = int(value[3])

        return {
            "enabled": enabled,
            "minutes": minutes,
            "rpm": rpm,
        }

    def airing_mode_write(enabled: bool, minutes: int, rpm: int):
        return pack(
            "<3BH", enabled, 26, h.validated_time(minutes), h.validated_rpm(rpm)
        )

    def boost_read(self, value):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")
        value = unpack("<B2H", value)

        enabled = bool(value[0])
        rpm = int(value[1])
        seconds = int(value[2])

        return {"enabled": enabled, "seconds": seconds, "rpm": rpm}

    def boost_write(enabled: bool, minutes: int, rpm: int):
        return pack("<2B", enabled, h.validated_time(minutes), h.validated_rpm(rpm))

    def constant_speed_read(self, value):
        if len(value) != 3:
            raise ValueError(f"Length need to be exactly 3, was {len(value)}.")
        value = unpack("<BH", value)

        enabled = bool(value[0])
        rpm = int(value[1])

        return {"enabled": enabled, "rpm": rpm}

    def constant_speed_write(enabled: bool, rpm: int):
        return pack("<BH", enabled, h.validated_rpm(rpm))

    def humidity_mode_read(self, value):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<BBH", value)

        enabled = bool(value[0])
        detection = int(value[1])
        rpm = int(value[2])

        return {
            "enabled": enabled,
            "detection": detection,
            "detection_description": self.detection_as_string(detection),
            "rpm": rpm,
        }

    def humidity_mode_write(enabled: bool, detection: int, rpm: int):
        return pack(
            "<BBH", enabled, h.validated_detection(detection), h.validated_rpm(rpm)
        )

    def light_and_voc_read(self, value):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<4B", value)

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
        light_enabled: bool, light_detection: int, voc_enabled: bool, voc_detection: int
    ):
        return pack(
            "<4b",
            bool(light_enabled),
            h.validated_detection(light_detection),
            bool(voc_enabled),
            h.validated_detection(voc_detection),
        )

    def pause_read(self, value):
        if len(value) != 2:
            raise ValueError(f"Length need to be exactly 2, was {len(value)}.")

        value = unpack("<2B", value)

        enabled = bool(value[0])
        minutes = int(value[1])

        return {"enabled": enabled, "minutes": minutes}

    def pause_write(enabled: bool, minutes: int):
        return pack("<2B", enabled, h.validated_time(minutes))

    def temporary_speed_write(enabled: bool, rpm: int):
        return pack("<BH", enabled, h.validated_rpm(rpm))

    def timer_read(self, value):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<3BH", value)

        minutes = int(value[0])
        delay_enabled = bool(value[1])
        delay_minutes = int(value[2])
        rpm = int(value[3])

        return {
            "delay": {"enabled": delay_enabled, "minutes": delay_minutes},
            "minutes": minutes,
            "rpm": rpm,
        }

    def timer_write(minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int):
        return pack(
            "<3BH",
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
