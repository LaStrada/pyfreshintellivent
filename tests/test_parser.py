"""Tests for SkyModeParser - parsing device mode data."""

import pytest

from pyfreshintellivent.parser import SkyModeParser

parser = SkyModeParser()


# Humidity mode tests
class TestHumidity:
    """Test humidity mode parsing."""

    def test_read_valid(self):
        valid = bytearray.fromhex("0102F401")
        val = parser.humidity_read(value=valid)
        assert val["enabled"] is True
        assert val["detection"] == "Medium"
        assert val["detection_raw"] == 2
        assert val["rpm"] == 500

        valid = bytearray.fromhex("0001E803")
        val = parser.humidity_read(value=valid)
        assert val["enabled"] is False
        assert val["detection"] == "Low"
        assert val["detection_raw"] == 1
        assert val["rpm"] == 1000

    def test_read_invalid_too_short(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.humidity_read(bytearray.fromhex("010101"))

    def test_read_invalid_too_long(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.humidity_read(bytearray.fromhex("0101010101"))

    def test_write_valid(self):
        val = parser.humidity_write(enabled=True, detection="Medium", rpm=800)
        assert val == bytearray.fromhex("01022003")


# Light and VOC mode tests
class TestLightAndVoc:
    """Test light and VOC mode parsing."""

    def test_read_valid(self):
        valid = bytearray.fromhex("01010101")
        val = parser.light_and_voc_read(value=valid)
        assert val["light"]["enabled"] is True
        assert val["light"]["detection"] == "Medium"
        assert val["light"]["detection_raw"] == 1
        assert val["voc"]["enabled"] is True
        assert val["voc"]["detection"] == "High"
        assert val["voc"]["detection_raw"] == 1

        valid = bytearray.fromhex("00020002")
        val = parser.light_and_voc_read(value=valid)
        assert val["light"]["enabled"] is False
        assert val["light"]["detection"] == "Medium"
        assert val["light"]["detection_raw"] == 2
        assert val["voc"]["enabled"] is False
        assert val["voc"]["detection"] == "Medium"
        assert val["voc"]["detection_raw"] == 2

    def test_read_invalid_too_short(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.light_and_voc_read(bytearray.fromhex("010101"))

    def test_read_invalid_too_long(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.light_and_voc_read(bytearray.fromhex("0101010101"))

    def test_write_valid(self):
        val = parser.light_and_voc_write(
            light_enabled=True,
            light_detection="Medium",
            voc_enabled=True,
            voc_detection="Medium",
        )
        assert val == bytearray.fromhex("01020102")


# Constant speed mode tests
class TestConstantSpeed:
    """Test constant speed mode parsing."""

    def test_read_valid(self):
        valid = bytearray.fromhex("013905")
        val = parser.constant_speed_read(value=valid)
        assert val["enabled"] is True
        assert val["rpm"] == 1337

        valid = bytearray.fromhex("000000")
        val = parser.constant_speed_read(value=valid)
        assert val["enabled"] is False
        assert val["rpm"] == 0

    def test_read_invalid_too_short(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.constant_speed_read(bytearray.fromhex("0101"))

    def test_read_invalid_too_long(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.constant_speed_read(bytearray.fromhex("0101010101"))

    def test_write_valid(self):
        val = parser.constant_speed_write(enabled=True, rpm=1337)
        assert val == bytearray.fromhex("013905")


# Timer mode tests
class TestTimer:
    """Test timer mode parsing."""

    def test_read_valid(self):
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

    def test_read_invalid_too_short(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.timer_read(bytearray.fromhex("00"))

    def test_read_invalid_too_long(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.timer_read(bytearray.fromhex("000000000000"))

    def test_write_valid(self):
        val = parser.timer_write(minutes=5, delay_enabled=True, delay_minutes=2, rpm=1000)
        assert val == bytearray.fromhex("050102E803")


# Airing mode tests
class TestAiring:
    """Test airing mode parsing."""

    def test_read_valid(self):
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

    def test_read_invalid_too_short(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.airing_read(bytearray.fromhex("0000"))

    def test_read_invalid_too_long(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.airing_read(bytearray.fromhex("000000000000"))

    def test_write_valid(self):
        val = parser.airing_write(enabled=True, minutes=30, rpm=1000)
        assert val == bytearray.fromhex("011a1EE803")


# Pause mode tests
class TestPause:
    """Test pause mode parsing."""

    def test_read_valid(self):
        valid = bytearray.fromhex("010a")
        val = parser.pause_read(valid)
        assert val["enabled"] is True
        assert val["minutes"] == 10

        valid = bytearray.fromhex("0000")
        val = parser.pause_read(value=valid)
        assert val["enabled"] is False
        assert val["minutes"] == 0

    def test_read_invalid_too_short(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.pause_read(bytearray.fromhex("00"))

    def test_read_invalid_too_long(self):
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.pause_read(bytearray.fromhex("000000"))

    def test_write_valid(self):
        val = parser.pause_write(enabled=True, minutes=10)
        assert val == bytearray.fromhex("010a")


# Boost mode tests
class TestBoost:
    """Test boost mode parsing."""

    def test_read_valid(self):
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

    def test_read_invalid_too_short(self):
        invalid = bytearray.fromhex("010101")
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.boost_read(value=invalid)

    def test_read_invalid_too_long(self):
        invalid = bytearray.fromhex("016009580200")
        with pytest.raises(ValueError, match=r"Length need to be exactly*"):
            parser.boost_read(value=invalid)

    def test_write_valid(self):
        val = parser.boost_write(enabled=True, seconds=600, rpm=2400)
        assert val == bytearray.fromhex("0160095802")


# Temporary speed mode tests
class TestTemporarySpeed:
    """Test temporary speed mode writing."""

    def test_write_valid(self):
        val = parser.temporary_speed_write(enabled=True, rpm=800)
        assert val == bytearray.fromhex("012003")

        val = parser.temporary_speed_write(enabled=False, rpm=1200)
        assert val == bytearray.fromhex("00B004")
