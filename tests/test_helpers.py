"""Tests for helper functions."""

import pytest

from pyfreshintellivent.helpers import (
    detection_int_as_string,
    detection_string_as_int,
    to_bytearray,
    validated_authentication_code,
    validated_detection,
    validated_rpm,
    validated_time,
)


def test_auth_code():
    """Test authentication code validation."""
    # Valid string input
    assert validated_authentication_code("00000000") == bytearray([0, 0, 0, 0])
    assert validated_authentication_code("01020304") == bytearray([1, 2, 3, 4])

    # Valid bytes/bytearray input
    assert validated_authentication_code(b"\x01\x02\x03\x04") == bytearray([1, 2, 3, 4])
    assert validated_authentication_code(bytearray([1, 2, 3, 4])) == bytearray(
        [1, 2, 3, 4]
    )

    # None input
    with pytest.raises(ValueError, match="Authentication code cannot be empty"):
        validated_authentication_code(None)

    # Wrong string length
    with pytest.raises(ValueError, match="Authentication code need to be 8 characters"):
        validated_authentication_code("aa")

    with pytest.raises(ValueError, match="Authentication code need to be 8 characters"):
        validated_authentication_code("aaaaaaaaaa")

    # Pairing mode check (all zeros)
    with pytest.raises(ValueError, match="Fan was not in pairing mode"):
        validated_authentication_code(bytearray(b"\x00\x00\x00\x00"))

    # Wrong bytes length
    with pytest.raises(ValueError, match="Authentication code need to be 4 bytes"):
        validated_authentication_code(b"\x01\x02")

    with pytest.raises(ValueError, match="Authentication code need to be 4 bytes"):
        validated_authentication_code(b"\x01\x02\x03\x04\x05")

    # Wrong type
    with pytest.raises(TypeError, match="Wrong type, expected bytes, bytearray or str"):
        validated_authentication_code(12345)


def test_rpm():
    """Test RPM validation."""
    assert validated_rpm(0) == 800
    assert validated_rpm(3000) == 2400
    assert validated_rpm(1200) == 1200


def test_detection():
    """Test detection value validation."""
    # Integer input
    assert validated_detection(-1) == 0
    assert validated_detection(0) == 0
    assert validated_detection(1) == 1
    assert validated_detection(2) == 2
    assert validated_detection(3) == 3
    assert validated_detection(4) == 3

    # String input - case insensitive
    assert validated_detection("Low") == 1
    assert validated_detection("low") == 1
    assert validated_detection("LOW") == 1
    assert validated_detection("Medium") == 2
    assert validated_detection("medium") == 2
    assert validated_detection("High") == 3
    assert validated_detection("high") == 3

    # Invalid string
    with pytest.raises(ValueError, match="is not a valid detection type"):
        validated_detection("Invalid")


def test_time():
    """Test time validation."""
    assert validated_time(0) == 0
    assert validated_time(100) == 100
    assert validated_time(-1) == 0


def test_detection_int_as_string():
    """Test detection integer to string conversion."""
    # Regular order
    assert detection_int_as_string(1) == "Low"
    assert detection_int_as_string(2) == "Medium"
    assert detection_int_as_string(3) == "High"

    # Reversed order
    assert detection_int_as_string(1, regular_order=False) == "High"
    assert detection_int_as_string(2, regular_order=False) == "Medium"
    assert detection_int_as_string(3, regular_order=False) == "Low"

    # With disable_low flag
    assert detection_int_as_string(1, regular_order=True, disable_low=True) == "Medium"
    assert detection_int_as_string(3, regular_order=False, disable_low=True) == "Medium"

    # Invalid value (should normalize via validated_detection)
    assert detection_int_as_string(0) == "Unknown"


def test_detection_string_as_int():
    """Test detection string to integer conversion."""
    # Regular order
    assert detection_string_as_int("Low") == 1
    assert detection_string_as_int("Medium") == 2
    assert detection_string_as_int("High") == 3

    # Case insensitive
    assert detection_string_as_int("low") == 1
    assert detection_string_as_int("MEDIUM") == 2

    # Reversed order
    assert detection_string_as_int("Low", regular_order=False) == 3
    assert detection_string_as_int("Medium", regular_order=False) == 2
    assert detection_string_as_int("High", regular_order=False) == 1

    # With disable_low flag
    assert detection_string_as_int("Low", disable_low=True) == 2

    # Invalid value should raise ValueError
    with pytest.raises(ValueError, match="is not a valid detection type"):
        detection_string_as_int("Invalid")


def test_to_bytearray():
    """Test bytearray conversion."""
    # From bytes
    assert to_bytearray(b"\x01\x02\x03") == bytearray([1, 2, 3])

    # From bytearray
    assert to_bytearray(bytearray([1, 2, 3])) == bytearray([1, 2, 3])

    # From hex string
    assert to_bytearray("010203") == bytearray([1, 2, 3])

    # Wrong type
    with pytest.raises(TypeError, match="Wrong type, expected bytes, bytearray or str"):
        to_bytearray(123)
