import pytest

from pyfreshintellivent import SkyModeParser


parser = SkyModeParser()


def test_detection_as_string():
    assert parser.detection_as_string(0) == "Unknown"
    assert parser.detection_as_string(1) == "Low"
    assert parser.detection_as_string(2) == "Medium"
    assert parser.detection_as_string(3) == "High"
    assert parser.detection_as_string(4) == "High"
    assert parser.detection_as_string(1, False) == "High"
    assert parser.detection_as_string(2, False) == "Medium"
    assert parser.detection_as_string(3, False) == "Low"
    assert parser.detection_as_string(4, False) == "Low"


def test_light_and_voc_valid():
    valid = bytearray.fromhex("01010101")
    val = parser.light_and_voc_read(value=valid)
    print(val)
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
    print(val)
    assert val["light"] is not None
    assert val["light"]["enabled"] is False
    assert val["light"]["detection"] == 3
    assert val["light"]["detection_description"] == "Low"

    assert val["voc"] is not None
    assert val["voc"]["enabled"] is False
    assert val["voc"]["detection"] == 3
    assert val["voc"]["detection_description"] == "High"


def test_light_and_voc_invalid():
    invalid = bytearray.fromhex("010101")
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.light_and_voc_read(value=invalid)

    invalid = bytearray.fromhex("0101010101")
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        parser.light_and_voc_read(value=invalid)


def test_humidity():
    valid = bytearray.fromhex("01013905")
    val = parser.humidity_mode_read(value=valid)
    print(val)
    assert val["enabled"] is True
    assert val["detection"] == 1
    assert val["detection_description"] == "Low"
    assert val["rpm"] == 1337

    valid = bytearray.fromhex("00030000")
    val = parser.humidity_mode_read(value=valid)
    print(val)
    assert val["enabled"] is False
    assert val["detection"] == 3
    assert val["detection_description"] == "High"
    assert val["rpm"] == 0
