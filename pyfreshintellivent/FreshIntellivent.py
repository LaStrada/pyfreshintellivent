from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from . import characteristics
from . import helpers as h
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

        # TODO: Add validation of authentication code
        await self._authenticate(authentication_code)

    async def _authenticate(self, authentication_code):
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH,
            data=bytes.fromhex(authentication_code)
        )
        self._log_message("Info", "Authenticated.")

    async def fetch_authentication_code(self, device: BleakClient):
        code = await device.read_gatt_char(char_specifier=characteristics.AUTH)
        return code

    async def _read_characterisitc(self, uuid):
        value = None
        try:
            value = await self.client.read_gatt_char(char_specifier=uuid)
        finally:
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
        value = unpack(
            "<BBH", await self._read_characterisitc(uuid=characteristics.HUMIDITY)
        )

        self.humidity_enabled = bool(value[0])
        self.humidity_detection = value[1]
        self.humidity_rpm = value[2]

        return {
            "enabled": self.humidity_enabled,
            "detection": self.humidity_detection,
            "rpm": self.humidity_rpm,
        }

    async def set_humidity(self, humidity_enabled, humidity_detection, humidity_rpm):
        value = (
            pack(
                "<BBH",
                humidity_enabled,
                h.validated_detection(humidity_detection),
                h.validated_rpm(humidity_rpm),
            ),
        )

        await self._write_characteristic(characteristics.HUMIDITY, value)

    async def get_light_and_voc(self):
        value = unpack(
            "<4B", await self._read_characterisitc(uuid=characteristics.LIGHT_VOC)
        )

        light_enabled = bool(value[0])
        light_detection = value[1]
        voc_enabled = bool(value[2])
        voc_detection = value[3]

        return {
            "light": {"enabled": light_enabled, "detection": light_detection},
            "voc": {"enabled": voc_enabled, "detection": voc_detection},
        }

    async def set_light_voc(
        self, light_enabled, light_detection, voc_enabled, voc_detection
    ):
        value = pack(
            "<4b",
            bool(light_enabled),
            h.validatedDetection(light_detection),
            bool(voc_enabled),
            h.validatedDetection(voc_detection),
        )

        await self._write_characteristic(characteristics.LIGHT_VOC, value)

    async def get_constant_speed(self):
        value = unpack(
            "<BH", await self._read_characterisitc(uuid=characteristics.CONSTANT_SPEED)
        )

        constant_speed_enabled = bool(value[0])
        constant_speed_rpm = value[1]

        return {"enabled": constant_speed_enabled, "rpm": constant_speed_rpm}

    async def set_constant_speed(self, constant_speed_enabled, constant_speed_rpm):
        value = pack("<BH", constant_speed_enabled, h.validatedRPM(constant_speed_rpm))

        await self._write_characteristic(characteristics.CONSTANT_SPEED, value)

    async def get_timer(self):
        value = unpack(
            "<3BH", await self._read_characterisitc(uuid=characteristics.TIMER)
        )

        timer_runningtime = value[0]
        timer_delay_enabled = bool(value[1])
        timer_delay_minutes = value[2]
        timer_rpm = value[3]

        return {
            "delay": {"enabled": timer_delay_enabled, "minutes": timer_delay_minutes},
            "runTime": timer_runningtime,
            "rpm": timer_rpm,
        }

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
        value = unpack(
            "<3BH", await self._read_characterisitc(uuid=characteristics.AIRING)
        )

        airing_enabled = bool(value[0])
        airing_run_time = value[2]
        airing_rpm = value[3]

        return {
            "enabled": airing_enabled,
            "runTime": airing_run_time,
            "rpm": airing_rpm,
        }

    async def set_airing(self, airing_enabled, airing_run_time, airing_rpm):
        value = pack(
            "<3BH",
            bool(airing_enabled),
            int(26),  # Always 1A? (= 26)
            h.validatedMinutes(airing_run_time),
            h.validatedRPM(airing_rpm),
        )

        await self._write_characteristic(characteristics.AIRING, value)

    async def get_pause(self):
        value = unpack(
            "<2B", await self._read_characterisitc(uuid=characteristics.PAUSE)
        )

        pause_enabled = bool(value[0])
        pause_minutes = value[1]

        return {"enabled": pause_enabled, "minutes": pause_minutes}

    async def set_pause(self, pause_enabled, pause_minutes):
        value = pack("<2B", bool(pause_enabled), h.validated_minutes(pause_minutes))

        await self._write_characteristic(characteristics.PAUSE, value)

    async def get_boost(self):
        value = unpack(
            "<B2H", await self._read_characterisitc(uuid=characteristics.BOOST)
        )

        boost_enabled = bool(value[0])
        boost_rpm = value[1]
        boost_seconds = value[2]

        return {"enabled": boost_enabled, "seconds": boost_seconds, "rpm": boost_rpm}

    async def set_boost(self, boost_enabled, boost_minutes, boost_rpm):
        value = pack(
            "<2B",
            bool(boost_enabled),
            h.validated_minutes(boost_minutes),
            h.validated_rpm(boost_rpm),
        )

        await self._write_characteristic(characteristics.BOOST, value)

    async def set_temporary_speed(self, temporary_enabled, temporary_rpm):
        value = pack("<BH", bool(temporary_enabled), h.validated_rpm(temporary_rpm))

        await self._write_characteristic(characteristics.TEMPORARY_SPEED, value)

    async def get_sensor_data(self):
        data = unpack(
            "<2B5HBH",
            await self._read_characterisitc(uuid=characteristics.DEVICE_STATUS),
        )
        return SkySensors(data)

class SkySensors:
    def __init__(self, data):
        if data is None or len(data) != 9:
            raise ValueError("Length of object need to be 9.")

        self._data = data

        self.status = bool(data[0])
        self.mode = data[1]
        self.rpm = data[5]
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
