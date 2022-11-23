import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_airing_read_valid():
    valid = bytearray.fromhex("01261EE803")
    val = parser.airing_read(valid)
    assert val["enabled"] is True
    assert val["minutes"] == 30
    assert val["rpm"] == 1000

    valid = bytearray.fromhex("00261E2003")
    val = parser.airing_read(valid)
    assert val["enabled"] is False
    assert val["minutes"] == 30
    assert val["rpm"] == 800


def test_timer_read_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.airing_read(bytearray.fromhex("0000"))


def test_timer_read_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.airing_read(bytearray.fromhex("000000000000"))


def test_timer_write_valid():
    val = parser.airing_write(enabled=True, minutes=30, rpm=1000)
    assert val == bytearray.fromhex("011a1EE803")
