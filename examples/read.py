"""Read a fan without putting its authentication key in arguments or output."""

import argparse
import asyncio
import os
from getpass import getpass

from bleak import BleakError, BleakScanner

from pyfreshintellivent import (
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventError,
)
from pyfreshintellivent.scanner import scan


async def main() -> int:
    """Read one snapshot using a private environment value or hidden prompt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", help="Known BLE address or platform UUID")
    parser.add_argument(
        "--authenticate", action="store_true", help="Prompt for an existing key"
    )
    args = parser.parse_args()
    key = (
        getpass("Authentication key (8 hex characters): ")
        if args.authenticate
        else os.environ.get("FRESH_AUTH_CODE")
    )
    try:
        reader = FreshIntelliventBluetoothDeviceData(
            authentication_code=key, max_attempts=1
        )
        device = (
            await BleakScanner.find_device_by_address(args.address, timeout=10)
            if args.address
            else await scan(timeout=10)
        )
        if device is None:
            print("No supported fan discovered.")
            return 1
        result = await reader.update_device(device)
    except (FreshIntelliventError, BleakError, ValueError) as err:
        print(
            f"Read failed ({type(err).__name__}). Check authentication and Bluetooth availability."
        )
        return 1
    print(f"Mode: {result.sensors.mode}")
    print(f"RPM: {result.sensors.rpm}")
    print(f"Temperature byte: {result.sensors.temperature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
