"""BLE device scanner for Fresh Intellivent Sky devices."""

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from . import consts


async def scan(timeout: float = 20.0) -> BLEDevice | None:
    """Scan for Fresh Intellivent Sky devices."""
    return await BleakScanner.find_device_by_filter(device_filter, timeout=timeout)


def device_filter(device: BLEDevice, advertisement_data: AdvertisementData) -> bool:
    """Filter BLE devices to identify Fresh Intellivent Sky devices."""
    # 0x180A is the standard Device Information service, not a Fresh identity.
    # Names are a discovery hint; successful protocol reads validate the device.
    return any(
        name and name.casefold() in consts.DISCOVERY_NAMES
        for name in (advertisement_data.local_name, device.name)
    )
