"""Sensor data model for Fresh Intellivent Sky devices."""

from __future__ import annotations

import dataclasses
from math import log
from struct import unpack

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


#  pylint: disable=too-many-instance-attributes
@dataclasses.dataclass
class SensorData:
    """Sensor readings from the device."""

    status: bool | None = None
    mode: str | None = None
    mode_raw: int | None = None
    temperature: float | None = None
    temperature_avg: float | None = None
    rpm: int | None = None
    humidity: float | None = None
    authenticated: bool | None = None
    unknowns: list[int] | None = None

    @classmethod
    def from_bytes(cls, data: bytes | bytearray) -> SensorData:
        """Parse raw sensor data from the device.

        Args:
            data: Raw 15-byte sensor data from device

        Returns:
            SensorData instance with parsed values

        Raises:
            ValueError: If data length is not exactly 15 bytes
        """
        if data is None or len(data) != 15:
            raise ValueError(f"Length need to be exactly 15, was {len(data)}.")

        values = unpack("<2B2H2B2H3B", data)

        status = bool(values[0])
        mode_raw = int(values[1])
        mode = _MODES.get(mode_raw, MODE_UNKNOWN)

        humidity = None
        if values[2] != 0:
            humidity = round((log(values[2] / 10) * 10), 1)

        temperature = values[3] / 100
        temperature_avg = values[7] / 100
        unknowns = [values[4], values[8], values[9], values[10]]
        authenticated = bool(values[5])
        rpm = values[6]

        return cls(
            status=status,
            mode=mode,
            mode_raw=mode_raw,
            temperature=temperature,
            temperature_avg=temperature_avg,
            rpm=rpm,
            humidity=humidity,
            authenticated=authenticated,
            unknowns=unknowns,
        )
