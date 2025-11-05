import pytest

from pyfreshintellivent.models import SensorData


def test_sensordata_valid():
    sensors = SensorData.from_bytes(bytearray.fromhex("00009001CE090000E8033C0A000000"))
    assert sensors.status is False
    assert sensors.temperature == 25.1
    assert sensors.rpm == 1000
    assert sensors.authenticated is False
    assert sensors.mode == "Off"
    assert sensors.mode_raw == 0

    sensors = SensorData.from_bytes(bytearray.fromhex("01003702E60Abd01D204040B001c00"))
    assert sensors.status is True
    assert sensors.temperature == 27.9
    assert sensors.rpm == 1234
    assert sensors.authenticated is True
    assert sensors.mode == "Off"
    assert sensors.mode_raw == 0


def test_sensordata_with_humidity():
    """Test SensorData with humidity value (non-zero)."""
    # Create data with humidity value 0x03E8 (1000) which should give log(100)*10
    # Format: status, mode, humidity(2), temp(2), unknown(1), auth(1), rpm(2), temp_avg(2), unknown(3)
    sensors = SensorData.from_bytes(bytearray.fromhex("0100E8030000000000000000000000"))
    assert sensors.humidity is not None
    assert sensors.humidity == 46.1  # round(log(1000/10) * 10, 1)

def test_sensordata_without_humidity():
    """Test SensorData without humidity (zero value)."""
    # Create data with humidity value 0x0000 (15 bytes total)
    sensors = SensorData.from_bytes(bytearray.fromhex("010000000000000000000000000000"))
    assert sensors.humidity is None





def test_sensordata_modes_known():
    # Off - 00
    sensors = SensorData.from_bytes(bytearray.fromhex("000090010000000000000000000000"))
    assert sensors.mode_raw == 0
    assert sensors.mode == "Off"

    # Pause - 06
    sensors = SensorData.from_bytes(bytearray.fromhex("000690010000000000000000000000"))
    assert sensors.mode_raw == 6
    assert sensors.mode == "Pause"

    # Constant speed - 16
    sensors = SensorData.from_bytes(bytearray.fromhex("001090010000000000000000000000"))
    assert sensors.mode_raw == 16
    assert sensors.mode == "Constant speed"

    # Light - 34
    sensors = SensorData.from_bytes(bytearray.fromhex("002290010000000000000000000000"))
    assert sensors.mode_raw == 34
    assert sensors.mode == "Light"

    # Timer - 35
    sensors = SensorData.from_bytes(bytearray.fromhex("002390010000000000000000000000"))
    assert sensors.mode_raw == 35
    assert sensors.mode == "Timer"

    # Humidity - 49
    sensors = SensorData.from_bytes(bytearray.fromhex("003190010000000000000000000000"))
    assert sensors.mode_raw == 49
    assert sensors.mode == "Humidity"

    # VOC - 52
    sensors = SensorData.from_bytes(bytearray.fromhex("003490010000000000000000000000"))
    assert sensors.mode_raw == 52
    assert sensors.mode == "VOC"

    # Boost - 103
    sensors = SensorData.from_bytes(bytearray.fromhex("006790010000000000000000000000"))
    assert sensors.mode_raw == 103
    assert sensors.mode == "Boost"


def test_sensordata_invalid_too_short():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        SensorData.from_bytes(bytearray.fromhex("0000900100000000000000000000"))


def test_sensordata_invalid_too_long():
    with pytest.raises(ValueError, match=r"Length need to be exactly*"):
        SensorData.from_bytes(bytearray.fromhex("00009001000000000000000000000000"))
