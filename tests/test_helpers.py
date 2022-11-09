import pytest

from pyfreshintellivent import helpers as h


def test_auth_code():
    assert h.validate_authentication_code("aaaaaaaa") is True

    with pytest.raises(ValueError):
        h.validate_authentication_code("zz")

    with pytest.raises(ValueError):
        h.validate_authentication_code("aa")

    with pytest.raises(ValueError):
        h.validate_authentication_code("aaaaaaaaaa")


def test_rpm():
    assert h.validated_rpm(0) == 800
    assert h.validated_rpm(3000) == 2400
    assert h.validated_rpm(1200) == 1200


def test_detection():
    assert h.validated_detection(-1) == 0
    assert h.validated_detection(0) == 0
    assert h.validated_detection(1) == 1
    assert h.validated_detection(2) == 2
    assert h.validated_detection(3) == 3
    assert h.validated_detection(4) == 3


def test_time():
    assert h.validated_time(0) == 0
    assert h.validated_time(100) == 100
    assert h.validated_time(-1) == 0
