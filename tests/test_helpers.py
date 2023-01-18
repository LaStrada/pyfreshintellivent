import pytest

from pyfreshintellivent.helpers import (
    to_hex,
    validated_authentication_code,
    validated_detection,
    validated_rpm,
    validated_time,
)


def test_auth_code():
    assert validated_authentication_code("00000000") == bytearray([0, 0, 0, 0])

    with pytest.raises(ValueError):
        validated_authentication_code("zz")

    with pytest.raises(ValueError):
        validated_authentication_code("aa")

    with pytest.raises(ValueError):
        validated_authentication_code("aaaaaaaaaa")

    with pytest.raises(ValueError):
        validated_authentication_code(None)


def test_rpm():
    assert validated_rpm(0) == 800
    assert validated_rpm(3000) == 2400
    assert validated_rpm(1200) == 1200


def test_detection():
    assert validated_detection(-1) == 0
    assert validated_detection(0) == 0
    assert validated_detection(1) == 1
    assert validated_detection(2) == 2
    assert validated_detection(3) == 3
    assert validated_detection(4) == 3


def test_time():
    assert validated_time(0) == 0
    assert validated_time(100) == 100
    assert validated_time(-1) == 0


def test_to_hex():
    assert to_hex("00") == "00"
    assert to_hex(bytearray([0, 0])) == "0000"
    assert to_hex(bytearray([0, 11])) == "000b"
    assert to_hex(bytearray([1])) == "01"
    assert to_hex(bytearray([255])) == "ff"
