"""Typed data models for Fresh Intellivent Sky devices."""

from __future__ import annotations

import dataclasses
from typing import Any


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

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class HumidityMode:
    """Humidity mode settings."""

    enabled: bool
    detection: str
    detection_raw: int
    rpm: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class LightSettings:
    """Light sensor settings."""

    enabled: bool
    detection: str
    detection_raw: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class VocSettings:
    """VOC sensor settings."""

    enabled: bool
    detection: str
    detection_raw: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class LightAndVocMode:
    """Light and VOC mode settings."""

    light: LightSettings
    voc: VocSettings

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return {
            "light": self.light.as_dict(),
            "voc": self.voc.as_dict(),
        }


@dataclasses.dataclass
class ConstantSpeedMode:
    """Constant speed mode settings."""

    enabled: bool
    rpm: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class DelaySettings:
    """Timer delay settings."""

    enabled: bool
    minutes: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TimerMode:
    """Timer mode settings."""

    delay: DelaySettings
    minutes: int
    rpm: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return {
            "delay": self.delay.as_dict(),
            "minutes": self.minutes,
            "rpm": self.rpm,
        }


@dataclasses.dataclass
class AiringMode:
    """Airing mode settings."""

    enabled: bool
    minutes: int
    rpm: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class PauseMode:
    """Pause mode settings."""

    enabled: bool
    minutes: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class BoostMode:
    """Boost mode settings."""

    enabled: bool
    seconds: int
    rpm: int

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        return dataclasses.asdict(self)


@dataclasses.dataclass
class DeviceModes:
    """All mode settings for the device."""

    humidity: HumidityMode | None = None
    light_and_voc: LightAndVocMode | None = None
    constant_speed: ConstantSpeedMode | None = None
    timer: TimerMode | None = None
    airing: AiringMode | None = None
    pause: PauseMode | None = None
    boost: BoostMode | None = None

    def as_dict(self) -> dict[str, Any]:
        """Convert to dict for backward compatibility."""
        result = {}
        if self.humidity:
            result["humidity"] = self.humidity.as_dict()
        if self.light_and_voc:
            result["light_and_voc"] = self.light_and_voc.as_dict()
        if self.constant_speed:
            result["constant_speed"] = self.constant_speed.as_dict()
        if self.timer:
            result["timer"] = self.timer.as_dict()
        if self.airing:
            result["airing"] = self.airing.as_dict()
        if self.pause:
            result["pause"] = self.pause.as_dict()
        if self.boost:
            result["boost"] = self.boost.as_dict()
        return result
