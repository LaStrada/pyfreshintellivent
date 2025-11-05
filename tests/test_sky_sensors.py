import pytest

from pyfreshintellivent.models import SensorData


def test_sensordata_valid():
    # TODO: Add humidity tests
    sensors = SensorData.from_bytes(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    assert sensors.status is False
    assert sensors.temperature == 25.1
    assert sensors.rpm == 1000
    assert sensors.authenticated is False
    assert sensors.mode == "Off"
    assert sensors.mode_raw == 0

    sensors = SensorData.from_bytes(bytearray.fromhex("01003702E60Abd01D204040B001c00"))
    assert sensors.status is True
    assert sensors.temperature == 27.9
    assert sensors.rpm == 1234
    assert sensors.authenticated is True
    assert sensors.mode == "Off"
    assert sensors.mode_raw == 0


def test_sensordata_dict():
    sensors = SensorData.from_bytes(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    sensor_dict = sensors.as_dict()
    assert sensor_dict["status"] is False
    assert sensor_dict["temperature"] == 25.1
    assert sensor_dict["rpm"] == 1000
    assert sensor_dict["authenticated"] is False
    assert sensor_dict["mode"] == "Off"
    assert sensor_dict["mode_raw"] == 0


def test_sensordata_modes_known():
    # Off - 00
    sensors = SensorData.from_bytes(bytearray.fromhex("000090010000000000000000000000"))
    assert sensors.mode_raw == 0
    assert sensors.mode == "Off"

    # Pause - 06
    sensors = SensorData.from_bytes(bytearray.fromhex("000690010000000000000000000000"))
    assert sensors.mode_raw == 6
    assert sensors.mode == "Pause"

    # Constant speed - 16
    sensors = SensorData.from_bytes(bytearray.fromhex("001090010000000000000000000000"))
    assert sensors.mode_raw == 16
    assert sensors.mode == "Constant speed"

    # Light - 34
    sensors = SensorData.from_bytes(bytearray.fromhex("002290010000000000000000000000"))
    assert sensors.mode_raw == 34
    assert sensors.mode == "Light"

    # Timer - 35
    sensors = SensorData.from_bytes(bytearray.fromhex("002390010000000000000000000000"))
    assert sensors.mode_raw == 35
    assert sensors.mode == "Timer"

    # Humidity - 49
    sensors = SensorData.from_bytes(bytearray.fromhex("003190010000000000000000000000"))
    assert sensors.mode_raw == 49
    assert sensors.mode == "Humidity"

    # VOC - 52
    sensors = SensorData.from_bytes(bytearray.fromhex("003490010000000000000000000000"))
    assert sensors.mode_raw == 52
    assert sensors.mode == "VOC"

    # Boost - 103
    sensors = SensorData.from_bytes(bytearray.fromhex("006790010000000000000000000000"))
    assert sensors.mode_raw == 103
    assert sensors.mode == "Boost"


def test_sensordata_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        SensorData.from_bytes(bytearray.fromhex("0000900100000000000000000000"))


def test_sensordata_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        SensorData.from_bytes(bytearray.fromhex("00009001000000000000000000000000"))
