"""Device information model for Fresh Intellivent Sky devices."""

from __future__ import annotations

import dataclasses

from .modes import DeviceModes
from .sensor_data import SensorData

DEVICE_MODEL = "Intellivent Sky"
MANUFACTURER = "Fresh"


@dataclasses.dataclass
class DeviceInfo:
    """Static device information (manufacturer, model, versions)."""

    manufacturer: str = MANUFACTURER
    model: str = DEVICE_MODEL
    hw_version: str | None = None
    sw_version: str | None = None
    fw_version: str | None = None


@dataclasses.dataclass
class FreshIntelliventDevice:
    """Representation of a Fresh Intellivent device."""

    name: str | None = None
    address: str | None = None
    info: DeviceInfo = dataclasses.field(default_factory=DeviceInfo)
    sensors: SensorData = dataclasses.field(default_factory=SensorData)
    modes: DeviceModes = dataclasses.field(default_factory=DeviceModes)
