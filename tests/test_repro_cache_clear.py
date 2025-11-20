
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from pyfreshintellivent.device import FreshIntelliventBluetoothDeviceData


@pytest.fixture
def ble_device():
    """Create a mock BLE device."""
    device = Mock(spec=BLEDevice)
    device.address = "AA:BB:CC:DD:EE:FF"
    device.name = "FreshSky"
    return device


@pytest.mark.asyncio
async def test_update_device_clears_cache_on_real_not_found_error(ble_device):
    """Test that characteristic cache is cleared when client raises 'not found'."""
    parser = FreshIntelliventBluetoothDeviceData()

    with patch("pyfreshintellivent.device.establish_connection") as mock_establish:
        mock_client = AsyncMock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        mock_client.clear_cache = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_establish.return_value = mock_client

        # Mock read_gatt_char to raise "not found"
        mock_client.read_gatt_char.side_effect = BleakError("characteristic not found")

        # The implementation propagates "not found" errors so callers can retry.
        with pytest.raises(BleakError):
            await parser._update_device(ble_device)

        mock_client.clear_cache.assert_awaited_once()
