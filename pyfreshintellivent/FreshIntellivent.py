import bluepy.btle as ble
from . import characteristics, helpers
from struct import pack, unpack

class Sky(object):

    def __init__(self, addr=None, auth=None, debug=False):
        self._auth = False
        self._debug = debug
        self._conn = ble.Peripheral()
        if addr is not None:
            self._conn.connect(addr=addr)
            if auth is not None:
                self.authenticate(auth)
        elif auth is not None and debug:
            print("[Fresh Intellivent Sky] [Warning] Can't authenticate when address is empty")

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        self._conn.disconnect()
        if self._debug:
            print("[Fresh Intellivent Sky] [Info] Disconnected")

    def connect(self, addr, auth):
        self._conn.connect(addr)
        if auth is not None:
            self.auth(auth)

    def fetchAuth(self):
        return self._readCharacterisitc(characteristics.AUTH)

    def authenticate(self, auth):
        if self._debug:
            print("[Fresh Intellivent Sky] [Info] Authenticating...")
        # TODO: Add logging when done authenticating

        try:
            self._conn.getCharacteristics(uuid=characteristics.AUTH)[0].write(
                bytes.fromhex(auth), withResponse=True)
            if self._debug:
                print("[Fresh Intellivent Sky] [Info] Authenticated!")
        except Exception as e:
            raise e
        else:
            self._auth = True

    def _readCharacterisitc(self, uuid):
        try:
            value = self._conn.getCharacteristics(uuid=uuid)[0].read()
            if self._debug:
                print("[Fresh Intellivent Sky] [R] {} = {}".format(uuid, value))
            return value
        except Exception as e:
            if self._debug:
                print("[Fresh Intellivent Sky] [Error] Read error - {}".format(str(e)))
            raise e

    def _writeCharacteristic(self, uuid, value):
        if (self._debug):
            print("[Fresh Intellivent Sky] [W] {} = {}".format(uuid, value))
        try:
            self._conn.getCharacteristics(uuid=uuid)[0].write(value, withResponse=True)
        except Exception as e:
            if self._debug:
                print("[Fresh Intellivent Sky] [Error] Write error - {}".format(str(e)))
            raise e

    def getHumidity(self):
        value = unpack('<BBH', self._readCharacterisitc(uuid=characteristics.HUMIDITY))
        self.humidityEnabled = bool(value[0])
        self.humidityDetection = value[1]
        self.humidityRPM = value[2]

        return {
            "enabled": self.humidityEnabled,
            "detection": self.humidityDetection,
            "rpm": self.humidityRPM
        }

    def setHumidity(self, humidityEnabled, humidityDetection, humidityRPM):
        value = pack('<BBH', humidityEnabled,
            validatedDetection(humidityDetection),
            validatedRPM(humidityRPM))
        self._writeCharacteristic(characteristics.HUMIDITY, value)

    def getLightVOC(self):
        value = unpack('<4B', self._readCharacterisitc(uuid=characteristics.LIGHT_VOC))
        lightEnabled = bool(value[0])
        lightDetection = value[1]
        vocEnabled = bool(value[2])
        vocDetection = value[3]

        return {
            "light": {
                "enabled": lightEnabled,
                "detection": lightDetection
            },
            "voc": {
                "enabled": vocEnabled,
                "detection": vocDetection
            }
        }

    def setLightVOC(self, lightEnabled, lightDetection, vocEnabled, vocDetection):
        value = pack('<4b',
            bool(lightEnabled),
            validatedDetection(lightDetection),
            bool(vocEnabled),
            validatedDetection(vocDetection))
        self._writeCharacteristic(characteristics.LIGHT_VOC, value)

    def getConstantSpeed(self):
        value = unpack('<BH', self._readCharacterisitc(uuid=characteristics.CONSTANT_SPEED))
        constantSpeedEnabled = bool(value[0])
        constantSpeedRPM = value[1]

        return {
            "enabled": constantSpeedEnabled,
            "rpm": constantSpeedRPM
        }

    def setConstantSpeed(self, constantSpeedEnabled, constantSpeedRPM):
        value = pack('<BH',
            constantSpeedEnabled,
            validatedRPM(constantSpeedRPM))
        self._writeCharacteristic(characteristics.CONSTANT_SPEED, value)

    def getTimer(self):
        value = unpack('<3BH', self._readCharacterisitc(uuid=characteristics.TIMER))
        timerRunningTime = value[0]
        timerDelayEnabled = bool(value[1])
        timerDelayMinutes = value[2]
        timerRPM = value[3]

        return {
            "delay": {
                "enabled": timerDelayEnabled,
                "minutes": timerDelayMinutes
            },
            "runTime": timerRunningTime,
            "rpm": timerRPM
        }

    def setTimer(self, timerRunningTime, timerDelayEnabled, timerDelayMinutes, timerRPM):
        value = pack('<3BH', timerRunningTime, bool(timerDelayEnabled), timerDelayMinutes, validatedRPM(timerRPM))
        self._writeCharacteristic(characteristics.TIMER, value)

    def getAiring(self):
        value = unpack('<3BH', self._readCharacterisitc(uuid=characteristics.AIRING))
        airingEnabled = bool(value[0])
        airingRunTime = value[2]
        airingRPM = value[3]

        return {
            "enabled": airingEnabled,
            "runTime": airingRunTime,
            "rpm": airingRPM
        }

    def setAiring(self, airingEnabled, airingRunTime, airingRPM):
        value = pack('<3BH',
            bool(airingEnabled),
            int(26), # Always 1A? (= 26)
            validatedMinutes(airingRunTime),
            validatedRPM(airingRPM))
        self._writeCharacteristic(characteristics.AIRING, value)

    def getPause(self):
        value = unpack('<2B', self._readCharacterisitc(uuid=characteristics.PAUSE))
        pauseEnabled = bool(value[0])
        pauseMinutes = value[1]

        return {
            "enabled": pauseEnabled,
            "minutes": pauseMinutes
        }

    def setPause(self, pauseEnabled, pauseMinutes):
        value = pack('<2B',
            bool(airingEnabled),
            validatedMinutes(pauseMinutes))
        self._writeCharacteristic(characteristics.PAUSE, value)

    def getBoost(self):
        value = unpack('<B2H', self._readCharacterisitc(uuid=characteristics.BOOST))
        boostEnabled = bool(value[0])
        boostMinutes = value[1]
        boostRPM = value[2]

        return {
            "enabled": boostEnabled,
            "minutes": boostMinutes,
            "rpm": boostRPM
        }

    def setBoost(self, boostEnabled, boostMinutes, boostRPM):
        value = pack('<2B',
            bool(boostEnabled),
            validatedMinutes(boostMinutes),
            validatedRPM(boostRPM))
        self._writeCharacteristic(CHARACTERISTIC_BOOST, value)

    def setTemporarySpeed(self, temporaryEnabled, temporaryRPM):
        value = pack('<BH',
            bool(temporaryEnabled),
            validatedRPM(temporaryRPM))
        self._writeCharacteristic(characteristics.TEMPORARY_SPEED, value)

    def getSensorData(self):
        value = unpack('<2B5HBH', self._readCharacterisitc(uuid=characteristics.DEVICE_STATUS))
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
            "mode": {
                "value": mode,
                "description": modeDescription
            },
            "secs": secs,
            "temp": temp
        }
