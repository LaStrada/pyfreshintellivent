import asyncio
import sys

from bleak import BleakScanner

from pyfreshintellivent import FreshIntelliVent


async def main():
    address = sys.argv[1]
    authentication_code = None
    if len(sys.argv) == 3:
        authentication_code = sys.argv[2]

    ble_device = await BleakScanner.find_device_by_address(address)

    client = FreshIntelliVent(ble_device)

    if ble_device is None:
        print("Couldn't find any devices")
        return

    try:
        print("Connecting...")
        await client.connect()
        print("Connected")

        await client.fetch_device_information()

        if authentication_code is None:
            print("No authentication code, skipping authentication")
        else:
            await client.authenticate(authentication_code=authentication_code)
            print("Authenticated")

        sensors = await client.fetch_sensor_data()
        print(f"Status: {sensors.as_dict()}")

        boost = await client.fetch_boost()
        print(f"Boost: {boost}")

        constant_speed = await client.fetch_constant_speed()
        print(f"Constant speed: {constant_speed}")

        humidity = await client.fetch_humidity()
        print(f"Humidity: {humidity}")

        light_and_voc = await client.fetch_light_and_voc()
        print(f"Light and VOC: {light_and_voc}")

        pause = await client.fetch_pause()
        print(f"Pause: {pause}")

        timer = await client.fetch_timer()
        print(f"Timer: {timer}")
    except Exception as e:
        await client.disconnect()
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
