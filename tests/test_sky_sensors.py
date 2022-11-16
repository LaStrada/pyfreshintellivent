import pytest

from pyfreshintellivent.sensors import SkySensors


def test_skysensors_valid():
    # TODO: Add humidity tests
    sensors = SkySensors(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    assert sensors.status is False
    assert sensors.temperature_1 == 25.1
    assert sensors.temperature_2 == 26.2
    assert sensors.rpm == 1000
    assert sensors.authenticated is False
    assert sensors.mode_description == "Off"
    assert sensors.mode == 0

    sensors = SkySensors(bytearray.fromhex("01003702E60Abd01D204040B001c00"))
    assert sensors.status is True
    assert sensors.temperature_1 == 27.9
    assert sensors.temperature_2 == 28.2
    assert sensors.rpm == 1234
    assert sensors.authenticated is True
    assert sensors.mode_description == "Off"
    assert sensors.mode == 0


def test_skysensors_dict():
    sensors = SkySensors(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    dict = sensors.as_dict()
    assert dict["status"] is False
    assert dict["temperatures"][0] == 25.1
    assert dict["temperatures"][1] == 26.2
    assert dict["rpm"] == 1000
    assert dict["authenticated"] is False
    assert dict["mode"]["description"] == "Off"
    assert dict["mode"]["raw_value"] == 0


def test_skysensors_modes_known():
    # Off - 00
    sensors = SkySensors(bytearray.fromhex("000090010000000000000000000000"))
    assert sensors.mode == 0
    assert sensors.mode_description == "Off"

    # Pause - 06
    sensors = SkySensors(bytearray.fromhex("000690010000000000000000000000"))
    assert sensors.mode == 6
    assert sensors.mode_description == "Pause"

    # Constant speed - 16
    sensors = SkySensors(bytearray.fromhex("001090010000000000000000000000"))
    assert sensors.mode == 16
    assert sensors.mode_description == "Constant speed"

    # Light - 34
    sensors = SkySensors(bytearray.fromhex("002290010000000000000000000000"))
    assert sensors.mode == 34
    assert sensors.mode_description == "Light"

    # Humidity - 49
    sensors = SkySensors(bytearray.fromhex("003190010000000000000000000000"))
    assert sensors.mode == 49
    assert sensors.mode_description == "Humidity"

    # VOC - 52
    sensors = SkySensors(bytearray.fromhex("003490010000000000000000000000"))
    assert sensors.mode == 52
    assert sensors.mode_description == "VOC"

    # Boost - 103
    sensors = SkySensors(bytearray.fromhex("006790010000000000000000000000"))
    assert sensors.mode == 103
    assert sensors.mode_description == "Boost"


def test_skysensors_modes_unknowns():
    sensors = SkySensors(bytearray.fromhex("000190010000000000000000000000"))
    assert sensors.mode == 1
    assert sensors.mode_description == "Unknown"

    sensors = SkySensors(bytearray.fromhex("000390010000000000000000000000"))
    assert sensors.mode == 3
    assert sensors.mode_description == "Unknown"

    sensors = SkySensors(bytearray.fromhex("006890010000000000000000000000"))
    assert sensors.mode == 104
    assert sensors.mode_description == "Unknown"

    sensors = SkySensors(bytearray.fromhex("00FF90010000000000000000000000"))
    assert sensors.mode == 255
    assert sensors.mode_description == "Unknown"


def test_skysensors_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        SkySensors(bytearray.fromhex("0000900100000000000000000000"))


def test_skysensors_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        SkySensors(bytearray.fromhex("00009001000000000000000000000000"))
