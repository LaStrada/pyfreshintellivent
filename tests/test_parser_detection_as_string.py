from pyfreshintellivent.helpers import detection_int_as_string, detection_string_as_int


def test_detection_int_as_string():
    assert detection_int_as_string(0) == "Unknown"
    assert detection_int_as_string(1) == "Low"
    assert detection_int_as_string(2) == "Medium"
    assert detection_int_as_string(3) == "High"
    assert detection_int_as_string(4) == "High"

    assert detection_int_as_string(1, False) == "High"
    assert detection_int_as_string(2, False) == "Medium"
    assert detection_int_as_string(3, False) == "Low"
    assert detection_int_as_string(4, False) == "Low"


def test_detection_string_as_int():
    assert detection_string_as_int("LOW") == 1
    assert detection_string_as_int("low") == 1
    assert detection_string_as_int("Medium") == 2
    assert detection_string_as_int("HiGh") == 3

    assert detection_string_as_int("Low", False) == 3
    assert detection_string_as_int("Medium", False) == 2
    assert detection_string_as_int("High", False) == 1
