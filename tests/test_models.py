"""Tests for typed data models."""

import pytest

from pyfreshintellivent.models import (
    DEVICE_MODEL,
    MANUFACTURER,
    AiringMode,
    BoostMode,
    ConstantSpeedMode,
    DelaySettings,
    DeviceInfo,
    DeviceModes,
    FreshIntelliventDevice,
    HumidityMode,
    LightAndVocMode,
    LightSettings,
    PauseMode,
    SensorData,
    TimerMode,
    VocSettings,
)


def test_device_info():
    """Test DeviceInfo model."""
    info = DeviceInfo()
    assert info.manufacturer == MANUFACTURER
    assert info.model == DEVICE_MODEL
    assert info.hw_version is None
    assert info.sw_version is None
    assert info.fw_version is None

    info = DeviceInfo(hw_version="1.0", sw_version="2.0", fw_version="3.0")
    assert info.hw_version == "1.0"
    assert info.sw_version == "2.0"
    assert info.fw_version == "3.0"


def test_fresh_intellivent_device():
    """Test FreshIntelliventDevice model."""
    device = FreshIntelliventDevice(name="Test Device", address="AA:BB:CC:DD:EE:FF")
    assert device.name == "Test Device"
    assert device.address == "AA:BB:CC:DD:EE:FF"
    assert isinstance(device.info, DeviceInfo)
    assert device.info.manufacturer == MANUFACTURER
    assert isinstance(device.sensors, SensorData)
    assert isinstance(device.modes, DeviceModes)


def test_sensor_data():
    """Test SensorData model."""
    sensor = SensorData(
        status=True,
        mode="Humidity",
        mode_raw=49,
        temperature=22.5,
        temperature_avg=21.8,
        rpm=1200,
        humidity=65.0,
        authenticated=True,
        unknowns=[0, 1, 2, 3],
    )

    assert sensor.temperature == 22.5
    assert sensor.rpm == 1200
    assert sensor.mode == "Humidity"

    # Test as_dict
    sensor_dict = sensor.as_dict()
    assert sensor_dict["temperature"] == 22.5
    assert isinstance(sensor_dict, dict)


def test_humidity_mode():
    """Test HumidityMode model."""
    mode = HumidityMode(enabled=True, detection="Medium", detection_raw=2, rpm=1500)

    assert mode.enabled is True
    assert mode.detection == "Medium"
    assert mode.rpm == 1500

    mode_dict = mode.as_dict()
    assert mode_dict["enabled"] is True


def test_light_and_voc_mode():
    """Test LightAndVocMode model."""
    light = LightSettings(enabled=True, detection="High", detection_raw=3)
    voc = VocSettings(enabled=False, detection="Low", detection_raw=1)
    mode = LightAndVocMode(light=light, voc=voc)

    assert mode.light.enabled is True
    assert mode.voc.enabled is False

    mode_dict = mode.as_dict()
    assert "light" in mode_dict
    assert "voc" in mode_dict
    assert mode_dict["light"]["detection"] == "High"


def test_constant_speed_mode():
    """Test ConstantSpeedMode model."""
    mode = ConstantSpeedMode(enabled=True, rpm=1800)

    assert mode.enabled is True
    assert mode.rpm == 1800


def test_timer_mode():
    """Test TimerMode model."""
    delay = DelaySettings(enabled=True, minutes=10)
    mode = TimerMode(delay=delay, minutes=30, rpm=2000)

    assert mode.delay.enabled is True
    assert mode.delay.minutes == 10
    assert mode.minutes == 30
    assert mode.rpm == 2000

    mode_dict = mode.as_dict()
    assert mode_dict["delay"]["minutes"] == 10


def test_airing_mode():
    """Test AiringMode model."""
    mode = AiringMode(enabled=False, minutes=15, rpm=1600)

    assert mode.enabled is False
    assert mode.minutes == 15


def test_pause_mode():
    """Test PauseMode model."""
    mode = PauseMode(enabled=True, minutes=5)

    assert mode.enabled is True
    assert mode.minutes == 5


def test_boost_mode():
    """Test BoostMode model."""
    mode = BoostMode(enabled=True, seconds=120, rpm=2400)

    assert mode.enabled is True
    assert mode.seconds == 120
    assert mode.rpm == 2400


def test_device_modes():
    """Test DeviceModes container."""
    humidity = HumidityMode(enabled=True, detection="Low", detection_raw=1, rpm=1000)
    modes = DeviceModes(humidity=humidity)

    assert modes.humidity is not None
    assert modes.humidity.rpm == 1000
    assert modes.boost is None

    # Test as_dict
    modes_dict = modes.as_dict()
    assert "humidity" in modes_dict
    assert "boost" not in modes_dict


def test_device_modes_as_dict_all_modes():
    """Test DeviceModes as_dict with all modes set."""
    modes = DeviceModes(
        humidity=HumidityMode(enabled=True, detection="Low", detection_raw=1, rpm=1000),
        constant_speed=ConstantSpeedMode(enabled=False, rpm=1200),
        pause=PauseMode(enabled=False, minutes=0),
        boost=BoostMode(enabled=False, seconds=0, rpm=2400),
    )

    modes_dict = modes.as_dict()
    assert "humidity" in modes_dict
    assert "constant_speed" in modes_dict
    assert "pause" in modes_dict
    assert "boost" in modes_dict
    assert "timer" not in modes_dict  # Not set
