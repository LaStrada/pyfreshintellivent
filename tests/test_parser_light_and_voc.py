import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_light_and_voc_valid():
    valid = bytearray.fromhex("01010101")
    val = parser.light_and_voc_read(value=valid)
    assert val["light"] is not None
    assert val["light"]["enabled"] is True
    assert val["light"]["detection"] == "Medium"
    assert val["light"]["detection_raw"] == 1

    assert val["voc"] is not None
    assert val["voc"]["enabled"] is True
    assert val["voc"]["detection"] == "High"
    assert val["voc"]["detection_raw"] == 1

    valid = bytearray.fromhex("00030003")
    val = parser.light_and_voc_read(value=valid)
    assert val["light"] is not None
    assert val["light"]["enabled"] is False
    assert val["light"]["detection"] == "High"
    assert val["light"]["detection_raw"] == 3

    assert val["voc"] is not None
    assert val["voc"]["enabled"] is False
    assert val["voc"]["detection"] == "Low"
    assert val["voc"]["detection_raw"] == 3


def test_light_and_voc_invalid_too_short():
    invalid = bytearray.fromhex("010101")
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.light_and_voc_read(value=invalid)


def test_light_and_voc_invalid_too_long():
    invalid = bytearray.fromhex("0101010101")
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.light_and_voc_read(value=invalid)


def test_light_and_voc_valid_write():
    val = parser.light_and_voc_write(
        light_enabled=True, light_detection=2, voc_enabled=True, voc_detection=3
    )
    assert val == bytearray.fromhex("01020103")
