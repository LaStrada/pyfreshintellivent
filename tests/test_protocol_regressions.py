"""Protocol checks independent of transport, including negative PIN replies."""

from unittest.mock import AsyncMock, patch

import pytest
from bleak.exc import BleakError

from pyfreshintellivent import characteristics
from pyfreshintellivent.device import (
    AuthenticationError,
    FreshIntelliventBluetoothDeviceData,
)
from pyfreshintellivent.parser import SkyModeParser


@pytest.mark.asyncio
@pytest.mark.parametrize("reply", [b"", b"\x00", b"\x02", b"\xff"])
async def test_negative_pin_confirmation(reply):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code="12345678")
    client = AsyncMock()
    client.read_gatt_char.return_value = reply
    with patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(AuthenticationError, match="rejected"):
            await reader.authenticate(client)
    client.read_gatt_char.assert_awaited_once_with(characteristics.AUTH_CONFIRMATION)


@pytest.mark.asyncio
async def test_pin_confirmation_transport_failure():
    reader = FreshIntelliventBluetoothDeviceData(authentication_code="12345678")
    client = AsyncMock()
    client.read_gatt_char.side_effect = BleakError("failed")
    with patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(AuthenticationError, match="exchange"):
            await reader.authenticate(client)


@pytest.mark.parametrize("raw,level", [(1, "Low"), (2, "Medium"), (3, "High")])
def test_voc_golden_values_and_roundtrip(raw, level):
    parser = SkyModeParser()
    packet = bytes([1, 2, 1, raw])
    assert parser.light_and_voc_read(packet)["voc"]["detection"] == level
    assert parser.light_and_voc_write(True, "Medium", True, level) == packet


def test_unknown_detection_is_not_clamped_to_high():
    parser = SkyModeParser()
    result = parser.light_and_voc_read(bytes([1, 255, 1, 254]))
    assert result["light"]["detection"] == "Unknown"
    assert result["light"]["detection_raw"] == 255
    assert result["voc"]["detection"] == "Unknown"
    assert result["voc"]["detection_raw"] == 254
