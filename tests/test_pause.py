import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_pause_read_valid():
    valid = bytearray.fromhex("010a")
    val = parser.pause_read(valid)
    assert val["enabled"] is True
    assert val["minutes"] == 10

    valid = bytearray.fromhex("0000")
    val = parser.pause_read(value=valid)
    print(val)
    assert val["enabled"] is False
    assert val["minutes"] == 0


def test_pause_read_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.pause_read(bytearray.fromhex("00"))


def test_pause_read_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.pause_read(bytearray.fromhex("000000"))


def test_pause_write_valid():
    val = parser.pause_write(enabled=True, minutes=10)
    assert val == bytearray.fromhex("010a")
