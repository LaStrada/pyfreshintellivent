"""Golden packets and exhaustive mode-nibble decoding regressions."""

import pytest

from pyfreshintellivent.models import SensorData


def test_packet_offsets_from_fresh_connect():
    # Distinct bytes at every position catch offset, width and endianness errors.
    sensor = SensorData.from_bytes(bytes.fromhex("a55434127856bc9af0de2143651809"))
    assert sensor.flags_raw == 0xA5
    assert sensor.mode_raw == 0x54
    assert sensor.active_trigger == 4
    assert sensor.motor_speed_code == 5
    assert sensor.mode == "VOC"
    assert sensor.humidity_raw == 0x1234
    assert sensor.voc_raw == 0x5678
    assert sensor.light_raw == 0x9ABC
    assert sensor.rpm == 0xDEF0
    assert sensor.reference_raw == 0x4321
    assert sensor.minutes_active == 0x65
    assert sensor.temperature == 24
    assert sensor.error_code == 9
    assert not hasattr(sensor, "humidity")
    assert not hasattr(sensor, "authenticated")
    assert not hasattr(sensor, "temperature_avg")


def test_legacy_capture_no_longer_confuses_voc_with_temperature():
    sensor = SensorData.from_bytes(bytearray.fromhex("01003702e60abd01d204040b001c00"))
    assert sensor.voc_raw == 2790
    assert sensor.temperature == 28
    assert sensor.light_raw == 445
    assert sensor.reference_raw == 2820
    assert sensor.rpm == 1234


@pytest.mark.parametrize("motor", range(16))
@pytest.mark.parametrize(
    "trigger,mode",
    [
        (1, "Humidity"),
        (2, "Light"),
        (3, "Timer"),
        (4, "VOC"),
        (5, "Airing"),
        (6, "Pause"),
        (7, "Boost"),
        (8, "Motor test"),
        (9, "Humidity sinking"),
        (10, "Unknown"),
        (11, "Delayed start"),
        (12, "Unknown"),
        (13, "Unknown"),
        (14, "Unknown"),
        (15, "Unknown"),
    ],
)
def test_trigger_independent_of_motor_speed(motor, trigger, mode):
    sensor = SensorData.from_bytes(bytes([0, motor << 4 | trigger]) + bytes(13))
    assert sensor.mode == mode
    assert sensor.active_trigger == trigger
    assert sensor.motor_speed_code == motor


@pytest.mark.parametrize(
    "motor,mode", [(0, "Off"), (1, "Constant speed"), (2, "Unknown"), (15, "Unknown")]
)
def test_no_trigger_uses_motor_code(motor, mode):
    sensor = SensorData.from_bytes(bytes([0, motor << 4]) + bytes(13))
    assert sensor.mode == mode


@pytest.mark.parametrize("length", [0, 1, 14, 16, 32])
def test_reject_malformed_packet(length):
    with pytest.raises(ValueError, match="exactly 15"):
        SensorData.from_bytes(bytes(length))
