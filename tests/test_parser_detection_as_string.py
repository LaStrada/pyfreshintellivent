from pyfreshintellivent import helpers as h


def test_detection_int_as_string():
    assert h.detection_int_as_string(0) == "Unknown"
    assert h.detection_int_as_string(1) == "Low"
    assert h.detection_int_as_string(2) == "Medium"
    assert h.detection_int_as_string(3) == "High"
    assert h.detection_int_as_string(4) == "High"

    assert h.detection_int_as_string(1, False) == "High"
    assert h.detection_int_as_string(2, False) == "Medium"
    assert h.detection_int_as_string(3, False) == "Low"
    assert h.detection_int_as_string(4, False) == "Low"


def test_detection_string_as_int():
    assert h.detection_string_as_int("LOW") == 1
    assert h.detection_string_as_int("low") == 1
    assert h.detection_string_as_int("Medium") == 2
    assert h.detection_string_as_int("HiGh") == 3

    assert h.detection_string_as_int("Low", False) == 3
    assert h.detection_string_as_int("Medium", False) == 2
    assert h.detection_string_as_int("High", False) == 1
