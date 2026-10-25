"""SKY sensor packet decoding."""

from __future__ import annotations

import dataclasses
from struct import unpack

MODE_UNKNOWN = "Unknown"
_TRIGGER_MODES = {
    1: "Humidity",
    2: "Light",
    3: "Timer",
    4: "VOC",
    5: "Airing",
    6: "Pause",
    7: "Boost",
    8: "Motor test",
    9: "Humidity sinking",
    11: "Delayed start",
}
_IDLE_MODES = {0: "Off", 1: "Constant speed"}


# pylint: disable=too-many-instance-attributes
@dataclasses.dataclass
class SensorData:
    """Sensor snapshot; raw humidity, light and VOC values have unknown units."""

    flags_raw: int | None = None
    mode: str | None = None
    mode_raw: int | None = None
    active_trigger: int | None = None
    motor_speed_code: int | None = None
    temperature: int | None = None
    rpm: int | None = None
    humidity_raw: int | None = None
    voc_raw: int | None = None
    light_raw: int | None = None
    reference_raw: int | None = None
    minutes_active: int | None = None
    error_code: int | None = None

    @classmethod
    def from_bytes(cls, data: bytes | bytearray) -> SensorData:
        """Decode a 15-byte SKY sensor packet."""
        if len(data) != 15:
            raise ValueError(f"Length must be exactly 15, was {len(data)}.")

        flags, mode_raw, humidity, voc, light, rpm, reference, minutes, temp, error = (
            unpack("<BB5H3B", data)
        )
        trigger = mode_raw & 0x0F
        motor = mode_raw >> 4
        mode = (
            _TRIGGER_MODES.get(trigger, MODE_UNKNOWN)
            if trigger
            else _IDLE_MODES.get(motor, MODE_UNKNOWN)
        )
        return cls(
            flags_raw=flags,
            mode=mode,
            mode_raw=mode_raw,
            active_trigger=trigger,
            motor_speed_code=motor,
            temperature=temp,
            rpm=rpm,
            humidity_raw=humidity,
            voc_raw=voc,
            light_raw=light,
            reference_raw=reference,
            minutes_active=minutes,
            error_code=error,
        )
