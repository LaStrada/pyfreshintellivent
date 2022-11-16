import pytest

from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_light_and_voc_valid():
    valid = bytearray.fromhex("01010101")
    val = parser.light_and_voc_read(value=valid)
    assert val["light"] is not None
    assert val["light"]["enabled"] is True
    assert val["light"]["detection"] == 1
    assert val["light"]["detection_description"] == "High"

    assert val["voc"] is not None
    assert val["voc"]["enabled"] is True
    assert val["voc"]["detection"] == 1
    assert val["voc"]["detection_description"] == "Low"

    valid = bytearray.fromhex("00030003")
    val = parser.light_and_voc_read(value=valid)
    assert val["light"] is not None
    assert val["light"]["enabled"] is False
    assert val["light"]["detection"] == 3
    assert val["light"]["detection_description"] == "Low"

    assert val["voc"] is not None
    assert val["voc"]["enabled"] is False
    assert val["voc"]["detection"] == 3
    assert val["voc"]["detection_description"] == "High"


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
