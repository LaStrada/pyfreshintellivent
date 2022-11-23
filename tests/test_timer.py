import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_timer_read_valid():
    valid = bytearray.fromhex("050102E803")
    val = parser.timer_read(valid)
    assert val["minutes"] == 5
    assert val["delay"]["enabled"] is True
    assert val["delay"]["minutes"] == 2
    assert val["rpm"] == 1000

    valid = bytearray.fromhex("0a00052003")
    val = parser.timer_read(valid)
    assert val["minutes"] == 10
    assert val["delay"]["enabled"] is False
    assert val["delay"]["minutes"] == 5
    assert val["rpm"] == 800


def test_timer_read_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.timer_read(bytearray.fromhex("00"))


def test_timer_read_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.timer_read(bytearray.fromhex("000000000000"))


def test_timer_write_valid():
    val = parser.timer_write(minutes=5, delay_enabled=True, delay_minutes=2, rpm=1000)
    assert val == bytearray.fromhex("050102E803")
