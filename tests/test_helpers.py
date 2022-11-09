import pytest

from pyfreshintellivent.helpers import (validate_authentication_code,
                                        validated_detection, validated_rpm,
                                        validated_time)


def test_auth_code():
    assert validate_authentication_code("aaaaaaaa") is True

    with pytest.raises(ValueError):
        validate_authentication_code("zz")

    with pytest.raises(ValueError):
        validate_authentication_code("aa")

    with pytest.raises(ValueError):
        validate_authentication_code("aaaaaaaaaa")


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
