from pyfreshintellivent.skyModeParser import SkyModeParser

parser = SkyModeParser()


def test_detection_as_string():
    assert parser.detection_as_string(0) == "Unknown"
    assert parser.detection_as_string(1) == "Low"
    assert parser.detection_as_string(2) == "Medium"
    assert parser.detection_as_string(3) == "High"
    assert parser.detection_as_string(4) == "High"
    assert parser.detection_as_string(1, False) == "High"
    assert parser.detection_as_string(2, False) == "Medium"
    assert parser.detection_as_string(3, False) == "Low"
    assert parser.detection_as_string(4, False) == "Low"
