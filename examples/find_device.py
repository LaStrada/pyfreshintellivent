import asyncio
import sys

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from pyfreshintellivent import device_filter

AUTHENTICATE_UUID = "4cad343a-209a-40b7-b911-4d9b3df569b2"
SENSOR_UUID = "528b80e8-c47a-4c0a-bdf1-916a7748f412"


async def main():
    print("Scanning, please wait...")

    device = await BleakScanner.find_device_by_filter(device_filter, timeout=20.0)
    if device is None:
        print("no matching device found, you may need to edit match_nus_uuid().")
        sys.exit(1)
    else:
        print(device)


if __name__ == "__main__":
    asyncio.run(main())
