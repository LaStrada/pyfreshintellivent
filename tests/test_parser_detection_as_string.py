from pyfreshintellivent import SkyModeParser

parser = SkyModeParser()


def test_detection_int_as_string():
    assert parser.detection_int_as_string(0) == "Unknown"
    assert parser.detection_int_as_string(1) == "Low"
    assert parser.detection_int_as_string(2) == "Medium"
    assert parser.detection_int_as_string(3) == "High"
    assert parser.detection_int_as_string(4) == "High"

    assert parser.detection_int_as_string(1, False) == "High"
    assert parser.detection_int_as_string(2, False) == "Medium"
    assert parser.detection_int_as_string(3, False) == "Low"
    assert parser.detection_int_as_string(4, False) == "Low"

def test_detection_string_as_int():
    assert parser.detection_string_as_int("LOW") == 1
    assert parser.detection_string_as_int("low") == 1
    assert parser.detection_string_as_int("Medium") == 2
    assert parser.detection_string_as_int("HiGh") == 3

    assert parser.detection_string_as_int("Low", False) == 3
    assert parser.detection_string_as_int("Medium", False) == 2
    assert parser.detection_string_as_int("High", False) == 1
