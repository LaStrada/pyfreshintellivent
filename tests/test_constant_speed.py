import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_constant_speed_read_valid():
    valid = bytearray.fromhex("013905")
    val = parser.constant_speed_read(value=valid)
    print(val)
    assert val["enabled"] is True
    assert val["rpm"] == 1337

    valid = bytearray.fromhex("000000")
    val = parser.constant_speed_read(value=valid)
    print(val)
    assert val["enabled"] is False
    assert val["rpm"] == 0


def test_constant_speed_read_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.constant_speed_read(bytearray.fromhex("0101"))


def test_constant_speed_read_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.constant_speed_read(bytearray.fromhex("0101010101"))


def test_constant_speed_write_valid():
    val = parser.constant_speed_write(enabled=True, rpm=1337)
    assert val == bytearray.fromhex("013905")
