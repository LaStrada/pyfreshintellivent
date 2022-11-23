import asyncio
import platform

from pyfreshintellivent import FreshIntelliVent

ADDRESS = (
    "mac-address"
    if platform.system() != "Darwin"
    else "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
)


async def main():
    sky = FreshIntelliVent()
    try:
        await sky.connect(address_or_ble_device=ADDRESS)
        await sky.authenticate(authentication_code="xxxxxxxx")

        sensors = await sky.get_sensor_data()
        print(f"Status: {sensors.as_dict()}")

        boost = await sky.get_boost()
        print(f"Boost: {boost}")

        constant_speed = await sky.get_constant_speed()
        print(f"Constant speed: {constant_speed}")

        humidity = await sky.get_humidity()
        print(f"Humidity: {humidity}")

        light_and_voc = await sky.get_light_and_voc()
        print(f"Light and VOC: {light_and_voc}")

        pause = await sky.get_pause()
        print(f"Pause: {pause}")

        timer = await sky.get_timer()
        print(f"Timer: {timer}")
    except Exception as e:
        print(e)
    finally:
        await sky.disconnect()


asyncio.run(main())
