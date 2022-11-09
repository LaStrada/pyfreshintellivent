from pyfreshintellivent.skyModeParser import detection_as_string


def test_detection_as_string():
    assert detection_as_string(0) == "Unknown"
    assert detection_as_string(1) == "Low"
    assert detection_as_string(2) == "Medium"
    assert detection_as_string(3) == "High"
    assert detection_as_string(4) == "High"
    assert detection_as_string(1, False) == "High"
    assert detection_as_string(2, False) == "Medium"
    assert detection_as_string(3, False) == "Low"
    assert detection_as_string(4, False) == "Low"
