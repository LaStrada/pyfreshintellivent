"""Example: Scan for Fresh Intellivent Sky devices.

Usage:
    python scan.py
"""

import asyncio

from pyfreshintellivent import scanner


async def main() -> int:
    """Scan for a device and print the result."""
    print("🔍 Scanning for Fresh Intellivent Sky devices (10s timeout)...")
    device = await scanner.scan(timeout=10.0)

    if device is None:
        print("❌ No device found.")
        return 1

    print(f"✅ Found: {device.name} ({device.address})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
