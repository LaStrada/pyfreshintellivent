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
        if bytes(code).hex() == "00000000":
            print("Could not fetch authentication code.")
            print("If this error persists, read how to enable pairing mode (step 1-3):")
            print(
                "https://github.com/LaStrada/pyfreshintellivent/blob/main/characteristics.md#Authenticate"
            )
        else:
            print(f"Authentication code: {bytes(code).hex()}")
    except Exception as e:
        print(e)
    finally:
        if client is not None:
            await client.disconnect()
            print("Disconnected")


asyncio.run(main())
