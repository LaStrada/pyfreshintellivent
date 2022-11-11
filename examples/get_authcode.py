import asyncio
import sys

from bleak import BleakClient, BleakScanner

from pyfreshintellivent import FreshIntelliVent

ADDRESS = "mac-address"


async def main():
    sky = FreshIntelliVent()
    try:
        device = await BleakScanner.find_device_by_address(
            device_identifier=ADDRESS, timeout=30.0
        )

        if device is None:
            print("no matching device found, check the BLE address.")
            sys.exit(1)

        client = BleakClient(device)
        await client.connect()
        print("Connected")

        code = await sky.fetch_authentication_code(device=client)
        print(f"Authentication code: {bytes(code).hex()}")
        await client.disconnect()
    except Exception as e:
        print(e)
    finally:
        await sky.disconnect()


asyncio.run(main())
