from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak.backends.device import BLEDevice

from pyfreshintellivent import characteristics, consts, scanner


def test_device_filter_matches_service_uuid():
    """Returns True when advertised UUID matches Fresh Intellivent service."""
    device = Mock(spec=BLEDevice)
    device.name = "Other"
    advertisement = SimpleNamespace(
        service_uuids=[str(characteristics.UUID_SERVICE)]
    )

    assert scanner.device_filter(device, advertisement) is True


def test_device_filter_matches_device_name():
    """Returns True when device name matches target name."""
    device = Mock(spec=BLEDevice)
    device.name = consts.DEVICE_NAME
    advertisement = SimpleNamespace(service_uuids=[])

    assert scanner.device_filter(device, advertisement) is True


def test_device_filter_no_match():
    """Returns False when neither UUID nor name match."""
    device = Mock(spec=BLEDevice)
    device.name = "Unrelated"
    advertisement = SimpleNamespace(service_uuids=[])

    assert scanner.device_filter(device, advertisement) is False


@pytest.mark.asyncio
async def test_scan_uses_filter_and_timeout():
    """scan delegates to BleakScanner.find_device_by_filter with our filter."""
    fake_device = Mock(spec=BLEDevice)
    with patch(
        "pyfreshintellivent.scanner.BleakScanner.find_device_by_filter",
        new_callable=AsyncMock,
    ) as mock_find:
        mock_find.return_value = fake_device

        result = await scanner.scan(timeout=12.3)

        assert result is fake_device
        mock_find.assert_awaited_once_with(scanner.device_filter, timeout=12.3)
