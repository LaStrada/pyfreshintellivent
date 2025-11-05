"""Typed data models for Fresh Intellivent Sky devices."""

from __future__ import annotations

from .device_info import FreshIntelliventDevice
from .modes import (
    AiringMode,
    BoostMode,
    ConstantSpeedMode,
    DelaySettings,
    DeviceModes,
    HumidityMode,
    LightAndVocMode,
    LightSettings,
    PauseMode,
    TimerMode,
    VocSettings,
)
from .sensor_data import SensorData

__all__ = [
    # Device
    "FreshIntelliventDevice",
    # Sensor Data
    "SensorData",
    # Modes
    "DeviceModes",
    "HumidityMode",
    "LightAndVocMode",
    "LightSettings",
    "VocSettings",
    "ConstantSpeedMode",
    "TimerMode",
    "DelaySettings",
    "AiringMode",
    "PauseMode",
    "BoostMode",
]
