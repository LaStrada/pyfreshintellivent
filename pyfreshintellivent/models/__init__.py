"""Typed data models for Fresh Intellivent Sky devices."""

from __future__ import annotations

from .device_info import DEVICE_MODEL, MANUFACTURER, DeviceInfo, FreshIntelliventDevice
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

# pylint: disable=duplicate-code  # Re-export pattern causes expected duplication
__all__ = [
    # Constants
    "DEVICE_MODEL",
    "MANUFACTURER",
    # Device
    "DeviceInfo",
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
