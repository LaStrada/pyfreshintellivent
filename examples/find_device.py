import asyncio
import sys

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

AUTHENTICATE_UUID = "4cad343a-209a-40b7-b911-4d9b3df569b2"
SENSOR_UUID = "528b80e8-c47a-4c0a-bdf1-916a7748f412"


async def main():
    print("Scanning, please wait...")

    def fresh(device: BLEDevice, adv: AdvertisementData):
        val = 0
        if AUTHENTICATE_UUID.lower() in adv.service_uuids:
            val = val + 1
            print("Found auth service!")

        if SENSOR_UUID.lower() in adv.service_uuids:
            val = val + 1
            print("Found sensor service!")

        if val == 2:
            print("This is it!")
            return True
        else:
            return False

    device = await BleakScanner.find_device_by_filter(fresh, timeout=20.0)
    if device is None:
        print("no matching device found, you may need to edit match_nus_uuid().")
        sys.exit(1)
    else:
        print(device)

    devices = await BleakScanner.discover(timeout=30, return_adv=True)
    for d, a in devices.values():
        print()
        print(d)
        print("-" * len(str(d)))
        print(a)


if __name__ == "__main__":
    asyncio.run(main())
