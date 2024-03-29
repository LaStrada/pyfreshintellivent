import pytest

from pyfreshintellivent.parser import SkyModeParser

parser = SkyModeParser()


def test_humidity_read_valid():
    valid = bytearray.fromhex("01013905")
    val = parser.humidity_read(value=valid)
    assert val["enabled"] is True
    assert val["detection"] == "Low"
    assert val["detection_raw"] == 1
    assert val["rpm"] == 1337

    valid = bytearray.fromhex("00030000")
    val = parser.humidity_read(value=valid)
    assert val["enabled"] is False
    assert val["detection"] == "High"
    assert val["detection_raw"] == 3
    assert val["rpm"] == 0


def test_humidity_read_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.humidity_read(bytearray.fromhex("010101"))


def test_humidity_read_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.humidity_read(bytearray.fromhex("0101010101"))


def test_humidity_write_valid():
    val = parser.humidity_write(enabled=True, detection="Low", rpm=1337)
    assert val == bytearray.fromhex("01013905")
