"""Sensor data parsing for Fresh Intellivent Sky devices."""

from math import log
from struct import unpack
from typing import Any, Union

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


class SkySensors:  # pylint: disable=too-many-instance-attributes
    """Sensor data container for Fresh Intellivent Sky devices."""

    mode: Union[str, None]
    mode_raw: Union[int, None]
    status: Union[bool, None]
    humidity: Union[float, None]
    temperature: Union[float, None]
    temperature_avg: Union[float, None]
    unknowns: Union[list[int], None]
    authenticated: Union[bool, None]
    rpm: Union[int, None]

    def parse_data(self, data: Union[bytes, bytearray]) -> None:
        """Parse raw sensor data from the device."""
        if data is None or len(data) != 15:
            raise ValueError(f"Length need to be exactly 15, was {len(data)}.")

        values = unpack("<2B2H2B2H3B", data)

        self.status = bool(values[0])
        self.mode_raw = int(values[1])
        if mode := _MODES.get(self.mode_raw):
            self.mode = mode
        else:
            self.mode = MODE_UNKNOWN

        if values[2] != 0:
            self.humidity = round((log(values[2] / 10) * 10), 1)
        self.temperature = values[3] / 100
        self.temperature_avg = values[7] / 100
        self.unknowns = [values[4], values[8], values[9], values[10]]
        self.authenticated = bool(values[5])

        self.rpm = values[6]

    def as_dict(
        self
    ) -> dict[str, Any]:
        """Return sensor data as a dictionary."""
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
