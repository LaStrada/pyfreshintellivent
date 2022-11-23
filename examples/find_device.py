import asyncio

from pyfreshintellivent import scanner

AUTHENTICATE_UUID = "4cad343a-209a-40b7-b911-4d9b3df569b2"
SENSOR_UUID = "528b80e8-c47a-4c0a-bdf1-916a7748f412"


async def main():
    print("Scanning, please wait...")
    device = await scanner.scan()
    print(f"Found device: {device}")


if __name__ == "__main__":
    asyncio.run(main())
