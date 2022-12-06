import asyncio
import sys
from bleak.backends.device import BLEDevice

from pyfreshintellivent import FreshIntelliVent


async def main():
    sky = FreshIntelliVent()
    address = sys.argv[1]
    authentication_code = sys.argv[2]

    ble_device = BLEDevice(address=address)

    try:
        async with sky.connect(ble_device) as client:
            await client.authenticate(authentication_code=authentication_code)

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
        print(e)


asyncio.run(main())
