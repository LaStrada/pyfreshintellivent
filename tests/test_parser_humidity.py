from pyfreshintellivent import SkyModeParser

parser = SkyModeParser()


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
