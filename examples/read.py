"""Example showing the new API for Fresh Intellivent Sky."""

import asyncio
import logging

from bleak import BleakScanner

from pyfreshintellivent import FreshIntelliventBluetoothDeviceData

logging.basicConfig(level=logging.INFO)


async def main():
    """Scan for device and read all data using the new API."""
    print("Scanning for Fresh Intellivent Sky devices...")
    
    # Scan for devices
    device = await BleakScanner.find_device_by_name("Intellivent SKY", timeout=10.0)
    
    if device is None:
        print("No device found!")
        return
    
    print(f"Found device: {device.name} ({device.address})")
    
    # Create parser with optional authentication
    # If your device requires authentication, provide the code:
    # parser = FreshIntelliventBluetoothDeviceData(authentication_code="your_code_here")
    parser = FreshIntelliventBluetoothDeviceData()
    
    # Connect, read all data, and disconnect automatically
    # The connection is properly managed and always closed
    fresh_device = await parser.update_device(device)
    
    # Display results
    print(f"\nDevice Information:")
    print(f"  Name: {fresh_device.name}")
    print(f"  Address: {fresh_device.address}")
    print(f"  Model: {fresh_device.model}")
    print(f"  Manufacturer: {fresh_device.manufacturer}")
    print(f"  Firmware: {fresh_device.fw_version}")
    print(f"  Hardware: {fresh_device.hw_version}")
    print(f"  Software: {fresh_device.sw_version}")
    
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
