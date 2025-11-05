"""Python interface for Fresh Intellivent Sky bathroom ventilation fan.

This is a major version rewrite with a modern, type-safe API.
The old FreshIntelliVent class has been removed in favor of
FreshIntelliventBluetoothDeviceData which provides better connection
management, full type safety, and automatic cleanup.
"""

from __future__ import annotations

from .device import (
    AuthenticationError,
    DisconnectedError,
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventDevice,
    FreshIntelliventError,
    FreshIntelliventTimeoutError,
    UnsupportedDeviceError,
)
from .models import (
    AiringMode,
    BoostMode,
    ConstantSpeedMode,
    DelaySettings,
    DeviceModes,
    HumidityMode,
    LightAndVocMode,
    LightSettings,
    PauseMode,
    SensorData,
    TimerMode,
    VocSettings,
)
from .parser import SkyModeParser

# Public API
__all__ = [
    # Main API
    "FreshIntelliventBluetoothDeviceData",
    "FreshIntelliventDevice",
    # Typed Models
    "SensorData",
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
    # Exceptions
    "FreshIntelliventError",
    "DisconnectedError",
    "AuthenticationError",
    "UnsupportedDeviceError",
    "FreshIntelliventTimeoutError",
    # Internal (exported for advanced usage)
    "SkyModeParser",
]
