import asyncio

from pyfreshintellivent import scanner


async def main():
    print("Scanning, please wait...")
    device = await scanner.scan()
    print(f"Found device: {device}")


if __name__ == "__main__":
    asyncio.run(main())
