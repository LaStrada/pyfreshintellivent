import asyncio
import sys

from bleak import BleakScanner

from pyfreshintellivent import FreshIntelliVent

TIMEOUT = 10.0


async def main():
    address = sys.argv[1]

    client = None

    try:
        device = await BleakScanner.find_device_by_address(
            device_identifier=address, timeout=TIMEOUT
        )

        if device is None:
            print("No matching device found, check the BLE address.")
            sys.exit(1)

        client = FreshIntelliVent(ble_device=device)
        await client.connect(timeout=TIMEOUT)
        print("Connected")

        code = await client.fetch_authentication_code()
        print(f"Authentication code: {bytes(code).hex()}")
        await client.disconnect()
    except Exception as e:
        print(e)
    finally:
        if client is not None:
            await client.disconnect()
            print("Disconnected")


asyncio.run(main())
