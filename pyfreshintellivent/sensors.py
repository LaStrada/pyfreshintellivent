from math import log
from struct import unpack
from typing import Union

MODE_OFF = "Off"
MODE_BOOST = "Boost"
MODE_CONSTANT_SPEED = "Constant speed"
MODE_HUMIDITY = "Humidity"
MODE_LIGHT = "Light"
MODE_PAUSE = "Pause"
MODE_VOC = "VOC"
MODE_UNKNOWN = "Unknown"


class SkySensors(object):
    def __init__(self):
        self._values = None

        self.status = None
        self.mode = None
        self.mode_description = None

        self.humidity = None
        self.temperature_1 = None
        self.temperature_2 = None
        self.unknowns = None
        self.authenticated = None

        self.rpm = None

    def parse_data(self, data: Union[bytes, bytearray]):
        if data is None or len(data) != 15:
            raise ValueError(f"Length need to be exactly 15, was {len(data)}.")

        values = unpack("<2B2H2B2H3B", data)

        self._values = values

        self.status = bool(values[0])
        self.mode = values[1]

        self.humidity = round((log(values[2] / 10) * 10), 1)
        self.temperature_1 = values[3] / 100
        self.temperature_2 = values[7] / 100
        self.unknowns = [values[4], values[8], values[9], values[10]]
        self.authenticated = bool(values[5])

        self.rpm = values[6]

        if self.mode == 0:
            self.mode_description = MODE_OFF
        elif self.mode == 6:
            self.mode_description = MODE_PAUSE
        elif self.mode == 16:
            self.mode_description = MODE_CONSTANT_SPEED
        elif self.mode == 34:
            self.mode_description = MODE_LIGHT
        elif self.mode == 49:
            self.mode_description = MODE_HUMIDITY
        elif self.mode == 52:
            self.mode_description = MODE_VOC
        elif self.mode == 103:
            self.mode_description = MODE_BOOST
        else:
            self.mode_description = MODE_UNKNOWN

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
