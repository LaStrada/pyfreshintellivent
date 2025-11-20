"""Example: Read all data from a Fresh Intellivent Sky device.

Usage:
    python read.py [--auth AUTH_CODE] [--address AA:BB:CC:DD:EE:FF]

Arguments:
    --auth       Optional authentication code (hex) if device is protected
    --address    Optional BLE address/UUID to connect directly (skip picker)

Examples:
    python read.py
    python read.py --auth 6f48b504
    python read.py --address AA:BB:CC:DD:EE:FF --auth 6f48b504
"""

import argparse
import asyncio
import logging
import sys

from bleak import BleakScanner

from pyfreshintellivent import (
    AuthenticationError,
    DisconnectedError,
    characteristics,
    consts,
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventError,
)

# Enable detailed logging to capture raw data
logging.basicConfig(
    level=logging.INFO,  # Keep console output concise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Read data from Fresh Intellivent Sky")
    parser.add_argument(
        "--auth",
        dest="auth_code",
        help="Authentication code (hex)",
    )
    parser.add_argument(
        "--address",
        dest="address",
        help="BLE address/UUID to connect directly",
    )
    return parser.parse_args()


async def main():
    """Scan for device and read all data using the new API."""
    args = parse_args()
    auth_code = args.auth_code
    address = args.address

    if auth_code:
        try:
            bytearray.fromhex(auth_code)
        except ValueError:
            print("❌ Invalid authentication code! Must be valid hexadecimal.")
            print(f"\nUsage: python {sys.argv[0]} [--auth AUTH_CODE]")
            print("\nExample: python read.py --auth 6f48b504")
            return 1
        print(f"🔐 Using authentication code: {auth_code}\n")

    if address:
        print(f"🔍 Searching for device at {address} (5s timeout)...")
        device = await BleakScanner.find_device_by_address(address, timeout=5.0)
        if device is None:
            print("❌ No device found at that address.")
            return 1
        print(f"✅ Found: {device.name} ({device.address})\n")
    else:
        print("🔍 Scanning for Fresh Intellivent Sky devices (10s timeout)...")
        discovered = await BleakScanner.discover(timeout=10.0)
        matches = []
        target_uuid = str(characteristics.UUID_SERVICE)
        for device in discovered:
            uuids = (
                device.metadata.get("uuids", []) if hasattr(device, "metadata") else []
            )
            if target_uuid in uuids or device.name == consts.DEVICE_NAME:
                matches.append(device)

        if not matches:
            print("❌ No device found!")
            print("\nTroubleshooting:")
            print("  - Is the device powered on?")
            print("  - Is Bluetooth enabled?")
            print("  - Is the device within range (< 10 meters)?")
            return 1

        if len(matches) == 1:
            device = matches[0]
            print(f"✅ Found: {device.name} ({device.address})\n")
        else:
            print("Multiple devices found:")
            for idx, device in enumerate(matches, start=1):
                print(f"  {idx}. {device.name} ({device.address})")
            selection = input(
                f"Select device [1-{len(matches)}] (default 1): "
            ).strip()
            try:
                selected_index = 1 if selection == "" else int(selection)
                if not 1 <= selected_index <= len(matches):
                    raise ValueError
            except ValueError:
                print("❌ Invalid selection.")
                return 1
            device = matches[selected_index - 1]
            print(f"\n✅ Selected: {device.name} ({device.address})\n")

    # Create parser with optional authentication
    parser = FreshIntelliventBluetoothDeviceData(
        authentication_code=auth_code
    )

    # Read all data (connection automatically managed!)
    print("📡 Reading device data...")

    try:
        fresh_device = await parser.update_device(device)
        print("✅ Successfully read all device data!\n")
    except DisconnectedError:
        print("❌ Device disconnected unexpectedly")
        return 1
    except AuthenticationError:
        print("❌ Authentication failed!")
        if auth_code:
            print("   The authentication code may be incorrect.")
        else:
            print("   This device requires an authentication code.")
            print(f"   Usage: python {sys.argv[0]} <AUTH_CODE>")
        return 1
    except FreshIntelliventError as e:
        print(f"❌ Error: {e}")
        return 1

    # Display results
    print("\nDevice Information:")
    print(f"  Name: {fresh_device.name}")
    print(f"  Address: {fresh_device.address}")
    print(f"  Model: {fresh_device.info.model}")
    print(f"  Manufacturer: {fresh_device.info.manufacturer}")
    print(f"  Firmware: {fresh_device.info.fw_version}")
    print(f"  Hardware: {fresh_device.info.hw_version}")
    print(f"  Software: {fresh_device.info.sw_version}")

    print("\nSensor Data:")
    # Now fully typed! IDE autocomplete works
    print(f"  Status: {fresh_device.sensors.status}")
    print(f"  Mode: {fresh_device.sensors.mode}")
    print(f"  Temperature: {fresh_device.sensors.temperature}°C")
    print(f"  Temperature (avg): {fresh_device.sensors.temperature_avg}°C")
    print(f"  Humidity: {fresh_device.sensors.humidity}%")
    print(f"  RPM: {fresh_device.sensors.rpm}")
    print(f"  Authenticated: {fresh_device.sensors.authenticated}")

    # Display mode settings (fully typed!)
    print("\nMode Settings:")

    if fresh_device.modes.humidity:
        mode = fresh_device.modes.humidity
        print(
            f"  Humidity: enabled={mode.enabled}, detection={mode.detection}, "
            f"rpm={mode.rpm}"
        )

    if fresh_device.modes.constant_speed:
        mode = fresh_device.modes.constant_speed
        print(f"  Constant Speed: enabled={mode.enabled}, rpm={mode.rpm}")

    if fresh_device.modes.boost:
        mode = fresh_device.modes.boost
        print(f"  Boost: enabled={mode.enabled}, seconds={mode.seconds}, "
              f"rpm={mode.rpm}")

    if fresh_device.modes.timer:
        mode = fresh_device.modes.timer
        print(
            f"  Timer: minutes={mode.minutes}, rpm={mode.rpm}, "
            f"delay={mode.delay.minutes}min"
        )

    # Can also convert to dict if needed
    # sensor_dict = fresh_device.sensors.as_dict()
    # modes_dict = fresh_device.modes.as_dict()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
