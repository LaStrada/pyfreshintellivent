from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak.backends.device import BLEDevice

from pyfreshintellivent import characteristics, consts, scanner


def test_generic_device_information_service_does_not_identify_fan():
    """The standard service UUID is also advertised by unrelated products."""
    device = Mock(spec=BLEDevice)
    device.name = "Other"
    advertisement = SimpleNamespace(
        local_name=None, service_uuids=[str(characteristics.UUID_SERVICE)]
    )

    assert scanner.device_filter(device, advertisement) is False


def test_device_filter_matches_device_name():
    """Returns True when device name matches target name."""
    device = Mock(spec=BLEDevice)
    device.name = consts.DEVICE_NAME
    advertisement = SimpleNamespace(local_name=None, service_uuids=[])

    assert scanner.device_filter(device, advertisement) is True


def test_device_filter_no_match():
    """Returns False when neither UUID nor name match."""
    device = Mock(spec=BLEDevice)
    device.name = "Unrelated"
    advertisement = SimpleNamespace(local_name=None, service_uuids=[])

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

        result = await scanner.scan(timeout=10.0)

        assert result is fake_device
        mock_find.assert_awaited_once_with(scanner.device_filter, timeout=10.0)


def test_device_filter_uses_current_advertisement_name():
    device = Mock(spec=BLEDevice, name=None)
    advertisement = SimpleNamespace(local_name=consts.DEVICE_NAME, service_uuids=[])
    assert scanner.device_filter(device, advertisement) is True


@pytest.mark.parametrize(
    "name", ["Intellivent SKY", "Intellivent Sky", "Intellivent ICE", "ICE"]
)
def test_discovery_known_sky_family_names(name):
    device = Mock(spec=BLEDevice, name=None)
    advertisement = SimpleNamespace(local_name=name, service_uuids=[])
    assert scanner.device_filter(device, advertisement) is True
