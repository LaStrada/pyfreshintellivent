import uu
import asyncio
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from . import characteristics
from . import helpers as h
from struct import pack, unpack


class Sky(object):
    def __init__(self, debug=False):
        self._debug = debug

    async def disconnect(self):
        await self.client.disconnect()
        self._log("Info", "Disconnected")

    async def connectAndAuthenticate(self, ble_address, authenticationCode):
        # TODO: Add validation of authentication code

        device = await BleakScanner.find_device_by_address(ble_address, timeout=20.0)
        if not device:
            raise BleakError(f"A device with address {ble_address} could not be found.")
        self._log("Info", f"Found {ble_address}")
        
        self.client = BleakClient(device)

        await self.client.connect()
        self._log("Info", f"Connected to {ble_address}")

        self._authenticate(authenticationCode)
    
    async def _authenticate(self, authenticationCode):
        # TODO: Catch errors
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH,
            data=bytes.fromhex(authenticationCode)
        )
        self._log("Info", "Authenticated")

    async def fetchAuthenticationCode(self, device: BleakClient):
        code = await device.read_gatt_char(
            char_specifier=characteristics.AUTH
        )
        return code

    async def _readCharacterisitc(self, uuid):
        value = await self.client.read_gatt_char(
            char_specifier=uuid
        )
        self._log("R", "{} = {}".format(uuid, value))
        return value

    async def _writeCharacteristic(self, uuid, value):
        self._log("W", "{} = {}".format(uuid, value))
        await self.client.write_gatt_char(
            char_specifier=characteristics.AUTH,
            data=bytes.fromhex(value)
        )
        # TODO: Handle errorw

    def _log(self, level, message):
        if self._debug:
            print(f"[Fresh Intellivent Sky] [{level}] {message}")

    async def getHumidity(self):
        # value = unpack("<BBH", self._readCharacterisitc(uuid=characteristics.HUMIDITY))
        if self.client.is_connected:
            humidity = await self._readCharacterisitc(uuid=characteristics.HUMIDITY)
            print(humidity)
        else:
            print("Not connected")

        # self.humidityEnabled = bool(value[0])
        # self.humidityDetection = value[1]
        # self.humidityRPM = value[2]

        # return {
        #     "enabled": self.humidityEnabled,
        #     "detection": self.humidityDetection,
        #     "rpm": self.humidityRPM,
        # }

    def setHumidity(self, humidityEnabled, humidityDetection, humidityRPM):
        value = (
            pack(
                "<BBH",
                humidityEnabled,
                h.validatedDetection(humidityDetection),
                h.validatedRPM(humidityRPM),
            ),
        )

        self._writeCharacteristic(characteristics.HUMIDITY, value)

    def getLightVOC(self):
        value = unpack("<4B", self._readCharacterisitc(uuid=characteristics.LIGHT_VOC))

        lightEnabled = bool(value[0])
        lightDetection = value[1]
        vocEnabled = bool(value[2])
        vocDetection = value[3]

        return {
            "light": {"enabled": lightEnabled, "detection": lightDetection},
            "voc": {"enabled": vocEnabled, "detection": vocDetection},
        }

    def setLightVOC(self, lightEnabled, lightDetection, vocEnabled, vocDetection):
        value = pack(
            "<4b",
            bool(lightEnabled),
            h.validatedDetection(lightDetection),
            bool(vocEnabled),
            h.validatedDetection(vocDetection),
        )

        self._writeCharacteristic(characteristics.LIGHT_VOC, value)

    def getConstantSpeed(self):
        value = unpack(
            "<BH", self._readCharacterisitc(uuid=characteristics.CONSTANT_SPEED)
        )

        constantSpeedEnabled = bool(value[0])
        constantSpeedRPM = value[1]

        return {"enabled": constantSpeedEnabled, "rpm": constantSpeedRPM}

    def setConstantSpeed(self, constantSpeedEnabled, constantSpeedRPM):
        value = pack("<BH", constantSpeedEnabled, h.validatedRPM(constantSpeedRPM))

        self._writeCharacteristic(characteristics.CONSTANT_SPEED, value)

    def getTimer(self):
        value = unpack("<3BH", self._readCharacterisitc(uuid=characteristics.TIMER))

        timerRunningTime = value[0]
        timerDelayEnabled = bool(value[1])
        timerDelayMinutes = value[2]
        timerRPM = value[3]

        return {
            "delay": {"enabled": timerDelayEnabled, "minutes": timerDelayMinutes},
            "runTime": timerRunningTime,
            "rpm": timerRPM,
        }

    def setTimer(
        self, timerRunningTime, timerDelayEnabled, timerDelayMinutes, timerRPM
    ):
        value = pack(
            "<3BH",
            timerRunningTime,
            bool(timerDelayEnabled),
            timerDelayMinutes,
            h.validatedRPM(timerRPM),
        )

        self._writeCharacteristic(characteristics.TIMER, value)

    def getAiring(self):
        value = unpack("<3BH", self._readCharacterisitc(uuid=characteristics.AIRING))

        airingEnabled = bool(value[0])
        airingRunTime = value[2]
        airingRPM = value[3]

        return {"enabled": airingEnabled, "runTime": airingRunTime, "rpm": airingRPM}

    def setAiring(self, airingEnabled, airingRunTime, airingRPM):
        value = pack(
            "<3BH",
            bool(airingEnabled),
            int(26),  # Always 1A? (= 26)
            h.validatedMinutes(airingRunTime),
            h.validatedRPM(airingRPM),
        )

        self._writeCharacteristic(characteristics.AIRING, value)

    def getPause(self):
        value = unpack("<2B", self._readCharacterisitc(uuid=characteristics.PAUSE))

        pauseEnabled = bool(value[0])
        pauseMinutes = value[1]

        return {"enabled": pauseEnabled, "minutes": pauseMinutes}

    def setPause(self, pauseEnabled, pauseMinutes):
        value = pack("<2B", bool(pauseEnabled), h.validatedMinutes(pauseMinutes))

        self._writeCharacteristic(characteristics.PAUSE, value)

    def getBoost(self):
        value = unpack("<B2H", self._readCharacterisitc(uuid=characteristics.BOOST))

        boostEnabled = bool(value[0])
        boostMinutes = value[1]
        boostRPM = value[2]

        return {"enabled": boostEnabled, "minutes": boostMinutes, "rpm": boostRPM}

    def setBoost(self, boostEnabled, boostMinutes, boostRPM):
        value = pack(
            "<2B",
            bool(boostEnabled),
            h.validatedMinutes(boostMinutes),
            h.validatedRPM(boostRPM),
        )

        self._writeCharacteristic(characteristics.BOOST, value)

    def setTemporarySpeed(self, temporaryEnabled, temporaryRPM):
        value = pack("<BH", bool(temporaryEnabled), h.validatedRPM(temporaryRPM))

        self._writeCharacteristic(characteristics.TEMPORARY_SPEED, value)

    def getSensorData(self):
        value = unpack(
            "<2B5HBH", self._readCharacterisitc(uuid=characteristics.DEVICE_STATUS)
        )

        status = bool(value[0])
        mode = value[1]
        rpm = value[5]
        secs = value[7]
        temp = value[8]

        modeDescription = "Unknown"
        if mode == 0:
            modeDescription = "Off"
        elif mode == 6:
            modeDescription = "Pause"
        elif mode == 16:
            modeDescription = "Constant speed"
        elif mode == 34:
            modeDescription = "Light"
        elif mode == 49:
            modeDescription = "Humidity"
        elif mode == 52:
            modeDescription = "VOC"
        elif mode == 103:
            modeDescription = "Boost"
        else:
            modeDescription = "Unknown ({})".format(mode)

        return {
            "status": status,
            "mode": {"value": mode, "description": modeDescription},
            "rpm": rpm,
            "secs": secs,
            "temp": temp,
        }
