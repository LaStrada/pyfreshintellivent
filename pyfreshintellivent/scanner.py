from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from . import characteristics, consts


async def scan(timeout: float = 20.0) -> BLEDevice | None:
    return await BleakScanner.find_device_by_filter(device_filter, timeout=timeout)


def device_filter(device: BLEDevice, advertisement_data: AdvertisementData) -> bool:
    uuids = advertisement_data.service_uuids
    if str(characteristics.UUID_SERVICE) in uuids:
        return True

    if device.name == consts.DEVICE_NAME:
        return True

    return False
