"""Mode data models for Fresh Intellivent Sky devices."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class HumidityMode:
    """Humidity mode settings."""

    enabled: bool
    detection: str
    detection_raw: int
    rpm: int


@dataclasses.dataclass
class LightSettings:
    """Light sensor settings."""

    enabled: bool
    detection: str
    detection_raw: int


@dataclasses.dataclass
class VocSettings:
    """VOC sensor settings."""

    enabled: bool
    detection: str
    detection_raw: int


@dataclasses.dataclass
class LightAndVocMode:
    """Light and VOC mode settings."""

    light: LightSettings
    voc: VocSettings


@dataclasses.dataclass
class ConstantSpeedMode:
    """Constant speed mode settings."""

    enabled: bool
    rpm: int


@dataclasses.dataclass
class DelaySettings:
    """Timer delay settings."""

    enabled: bool
    minutes: int


@dataclasses.dataclass
class TimerMode:
    """Timer mode settings."""

    delay: DelaySettings
    minutes: int
    rpm: int


@dataclasses.dataclass
class AiringMode:
    """Airing mode settings."""

    enabled: bool
    minutes: int
    rpm: int


@dataclasses.dataclass
class PauseMode:
    """Pause mode settings."""

    enabled: bool
    minutes: int


@dataclasses.dataclass
class BoostMode:
    """Boost mode settings."""

    enabled: bool
    seconds: int
    rpm: int


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
