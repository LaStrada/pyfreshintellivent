import pytest

from pyfreshintellivent.sensors import SkySensors

sensors = SkySensors()


def test_skysensors_valid():
    # TODO: Add humidity tests
    sensors.parse_data(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    assert sensors.status is False
    assert sensors.temperature == 25.1
    assert sensors.rpm == 1000
    assert sensors.authenticated is False
    assert sensors.mode == "Off"
    assert sensors.mode_raw == 0

    sensors.parse_data(bytearray.fromhex("01003702E60Abd01D204040B001c00"))
    assert sensors.status is True
    assert sensors.temperature == 27.9
    assert sensors.rpm == 1234
    assert sensors.authenticated is True
    assert sensors.mode == "Off"
    assert sensors.mode_raw == 0


def test_skysensors_dict():
    sensors.parse_data(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    dict = sensors.as_dict()
    assert dict["status"] is False
    assert dict["temperature"] == 25.1
    assert dict["rpm"] == 1000
    assert dict["authenticated"] is False
    assert dict["mode"] == "Off"
    assert dict["mode_raw"] == 0


def test_skysensors_modes_known():
    # Off - 00
    sensors.parse_data(bytearray.fromhex("000090010000000000000000000000"))
    assert sensors.mode_raw == 0
    assert sensors.mode == "Off"

    # Pause - 06
    sensors.parse_data(bytearray.fromhex("000690010000000000000000000000"))
    assert sensors.mode_raw == 6
    assert sensors.mode == "Pause"

    # Constant speed - 16
    sensors.parse_data(bytearray.fromhex("001090010000000000000000000000"))
    assert sensors.mode_raw == 16
    assert sensors.mode == "Constant speed"

    # Light - 34
    sensors.parse_data(bytearray.fromhex("002290010000000000000000000000"))
    assert sensors.mode_raw == 34
    assert sensors.mode == "Light"

    # Humidity - 49
    sensors.parse_data(bytearray.fromhex("003190010000000000000000000000"))
    assert sensors.mode_raw == 49
    assert sensors.mode == "Humidity"

    # VOC - 52
    sensors.parse_data(bytearray.fromhex("003490010000000000000000000000"))
    assert sensors.mode_raw == 52
    assert sensors.mode == "VOC"

    # Boost - 103
    sensors.parse_data(bytearray.fromhex("006790010000000000000000000000"))
    assert sensors.mode_raw == 103
    assert sensors.mode == "Boost"


def test_skysensors_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        sensors.parse_data(bytearray.fromhex("0000900100000000000000000000"))


def test_skysensors_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        sensors.parse_data(bytearray.fromhex("00009001000000000000000000000000"))
