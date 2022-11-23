import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_boost_valid():
    valid = bytearray.fromhex("0160095802")
    val = parser.boost_read(value=valid)
    assert val is not None
    assert val["enabled"] is True
    assert val["rpm"] == 2400
    assert val["seconds"] == 600

    valid = bytearray.fromhex("00D007F401")
    val = parser.boost_read(value=valid)
    assert val["enabled"] is False
    assert val["rpm"] == 2000
    assert val["seconds"] == 500


def test_boost_invalid_too_short():
    invalid = bytearray.fromhex("010101")
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.boost_read(value=invalid)


def test_boost_invalid_too_long():
    invalid = bytearray.fromhex("016009580200")
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.boost_read(value=invalid)


def test_boost_valid_write():
    val = parser.boost_write(enabled=True, seconds=600, rpm=2400)
    print(val)
    assert val == bytearray.fromhex("0160095802")
