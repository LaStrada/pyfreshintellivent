import pytest
from bleak.exc import BleakError

from pyfreshintellivent import FreshIntelliVent


@pytest.mark.asyncio
async def test_connect():
    mac = "aa:aa:aa:aa:aa"
    sky = FreshIntelliVent(mac)
    assert sky.ble_address == mac
    assert sky.is_connected() is False

    with pytest.raises(BleakError, match="Not connected"):
        await sky.authenticate("000000")

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_airing()
    with pytest.raises(BleakError, match="Not connected"):
        await sky.set_airing(enabled=False, minutes=10, rpm=1000)

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_light_and_voc()
    with pytest.raises(BleakError, match="Not connected"):
        # TODO: Is this correct?? RPM?
        await sky.set_light_and_voc(
            light_enabled=True, light_detection=1, voc_enabled=True, voc_detection=2
        )

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_constant_speed()
    with pytest.raises(BleakError, match="Not connected"):
        await sky.set_constant_speed(enabled=True, rpm=1000)

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_timer()
    with pytest.raises(BleakError, match="Not connected"):
        await sky.set_timer(minutes=10, delay_enabled=True, delay_minutes=2, rpm=1400)

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_pause()
    with pytest.raises(BleakError, match="Not connected"):
        await sky.set_pause(enabled=True, minutes=10)

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_boost()
    with pytest.raises(BleakError, match="Not connected"):
        await sky.set_boost(enabled=True, rpm=2400, seconds=600)

    with pytest.raises(BleakError, match="Not connected"):
        await sky.set_temporary_speed(enabled=False, rpm=1200)

    with pytest.raises(BleakError, match="Not connected"):
        await sky.get_sensor_data()
