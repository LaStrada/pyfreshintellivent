from math import log
from struct import unpack
from typing import Union


class SkySensors(object):
    def __init__(self, data: Union[bytes, bytearray]):
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
