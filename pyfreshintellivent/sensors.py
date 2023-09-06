from math import log
from struct import unpack
from typing import Union

MODE_UNKNOWN = "Unknown"

_MODES = {
    0: "Off",
    6: "Pause",
    16: "Constant speed",
    34: "Light",
    35: "Timer",
    49: "Humidity",
    52: "VOC",
    103: "Boost",
}


class SkySensors(object):
    def __init__(self):
        self._values = None

        self.status = None
        self.mode = None
        self.mode_raw = None

        self.humidity = None
        self.temperature = None
        self.temperature_avg = None
        self.unknowns = None
        self.authenticated = None

        self.rpm = None

    def parse_data(self, data: Union[bytes, bytearray]):
        if data is None or len(data) != 15:
            raise ValueError(f"Length need to be exactly 15, was {len(data)}.")

        values = unpack("<2B2H2B2H3B", data)

        self._values = values

        self.status = bool(values[0])
        self.mode_raw = int(values[1])
        if mode := _MODES.get(self.mode_raw):
            self.mode = mode
        else:
            self.mode = MODE_UNKNOWN

        self.humidity = round((log(values[2] / 10) * 10), 1)
        self.temperature = values[3] / 100
        self.temperature_avg = values[7] / 100
        self.unknowns = [values[4], values[8], values[9], values[10]]
        self.authenticated = bool(values[5])

        self.rpm = values[6]

    def as_dict(self):
        return {
            "status": self.status,
            "mode": self.mode,
            "mode_raw": self.mode_raw,
            "temperature": self.temperature,
            "temperature_avg": self.temperature_avg,
            "rpm": self.rpm,
            "humidity": self.humidity,
            "unknowns": self.unknowns,
            "authenticated": self.authenticated,
        }
