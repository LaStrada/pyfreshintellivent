"""Example: Read all data from Fresh Intellivent Sky device.

This example demonstrates the modern v2.0 API with:
- Automatic connection management (no manual connect/disconnect)
- Fully typed data models (complete IDE autocomplete)
- Automatic retry on transient failures
- Proper error handling

Usage:
    python read.py

Requirements:
    - Fresh Intellivent Sky device nearby
    - Device name must be "Intellivent SKY" (or modify the code)
    - Optional: Authentication code if device is protected
"""

import asyncio
import logging
import sys

from bleak import BleakScanner

from pyfreshintellivent import (
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventError,
    DisconnectedError,
    AuthenticationError,
)

# Optional: Enable debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


async def main():
    """Scan for device and read all data using the new API."""
    print("🔍 Scanning for Fresh Intellivent Sky devices...")
    print("   (This may take up to 10 seconds)\n")
    
    # Scan for devices by name
    device = await BleakScanner.find_device_by_name("Intellivent SKY", timeout=10.0)
    
    if device is None:
        print("❌ No device found!")
        print("\nTroubleshooting:")
        print("  - Is the device powered on?")
        print("  - Is Bluetooth enabled?")
        print("  - Is the device within range (< 10 meters)?")
        return 1
    
    print(f"✅ Found: {device.name} ({device.address})\n")
    
    # Create parser
    # For protected devices, add: authentication_code="your_code_here"
    parser = FreshIntelliventBluetoothDeviceData()
    
    # Read all data (connection automatically managed!)
    print("📡 Reading device data...")
    
    try:
        fresh_device = await parser.update_device(device)
        print("✅ Successfully read all device data!\n")
    except DisconnectedError:
        print("❌ Device disconnected unexpectedly")
        return 1
    except AuthenticationError:
        print("❌ Authentication failed (device may require auth code)")
        return 1
    except FreshIntelliventError as e:
        print(f"❌ Error: {e}")
        return 1
    
    # Display results
    print(f"\nDevice Information:")
    print(f"  Name: {fresh_device.name}")
    print(f"  Address: {fresh_device.address}")
    print(f"  Model: {fresh_device.info.model}")
    print(f"  Manufacturer: {fresh_device.info.manufacturer}")
    print(f"  Firmware: {fresh_device.info.fw_version}")
    print(f"  Hardware: {fresh_device.info.hw_version}")
    print(f"  Software: {fresh_device.info.sw_version}")
    
    print(f"\nSensor Data:")
    # Now fully typed! IDE autocomplete works
    print(f"  Status: {fresh_device.sensors.status}")
    print(f"  Mode: {fresh_device.sensors.mode}")
    print(f"  Temperature: {fresh_device.sensors.temperature}°C")
    print(f"  Temperature (avg): {fresh_device.sensors.temperature_avg}°C")
    print(f"  Humidity: {fresh_device.sensors.humidity}%")
    print(f"  RPM: {fresh_device.sensors.rpm}")
    print(f"  Authenticated: {fresh_device.sensors.authenticated}")
    
    # Display mode settings (fully typed!)
    print(f"\nMode Settings:")
    
    if fresh_device.modes.humidity:
        mode = fresh_device.modes.humidity
        print(f"  Humidity: enabled={mode.enabled}, detection={mode.detection}, rpm={mode.rpm}")
    
    if fresh_device.modes.constant_speed:
        mode = fresh_device.modes.constant_speed
        print(f"  Constant Speed: enabled={mode.enabled}, rpm={mode.rpm}")
    
    if fresh_device.modes.boost:
        mode = fresh_device.modes.boost
        print(f"  Boost: enabled={mode.enabled}, seconds={mode.seconds}, rpm={mode.rpm}")
    
    if fresh_device.modes.timer:
        mode = fresh_device.modes.timer
        print(f"  Timer: minutes={mode.minutes}, rpm={mode.rpm}, delay={mode.delay.minutes}min")
    
    # Can also convert to dict if needed
    # sensor_dict = fresh_device.sensors.as_dict()
    # modes_dict = fresh_device.modes.as_dict()


if __name__ == "__main__":
    asyncio.run(main())
