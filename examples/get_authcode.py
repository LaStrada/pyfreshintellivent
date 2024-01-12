import asyncio
import sys

from bleak import BleakScanner
import logging

from pyfreshintellivent import FreshIntelliVent

logging.basicConfig(level=logging.INFO)

TIMEOUT = 10.0


async def main():
    if len(sys.argv) <= 1:
        print("Please add the address as a parameter.")
        return
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

        code = await client.fetch_authentication_code()
        if bytes(code).hex() == "00000000":
            print("Could not fetch authentication code.")
            print("If this error persists, read how to enable pairing mode (step 1-3):")
            print(
                "https://github.com/LaStrada/pyfreshintellivent/blob/main/characteristics.md#Authenticate"  # noqa: E501
            )
        else:
            logging.info(f"Authentication code: {bytes(code).hex()}")
    except Exception as e:
        logging.error("Error: {}", e)
    finally:
        if client is not None:
            await client.disconnect()


asyncio.run(main())
