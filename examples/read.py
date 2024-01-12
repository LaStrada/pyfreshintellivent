import asyncio
import sys

from bleak import BleakScanner
import logging

from pyfreshintellivent import FreshIntelliVent


logging.basicConfig(level=logging.INFO)


async def main():
    if len(sys.argv) <= 1:
        print("Please add the address as a parameter.")
        return
    address = sys.argv[1]
    authentication_code = None
    if len(sys.argv) == 3:
        authentication_code = sys.argv[2]

    ble_device = await BleakScanner.find_device_by_address(address)

    if ble_device is None:
        logging.warn("Couldn't find the device")
        return

    client = FreshIntelliVent(ble_device)

    try:
        await client.connect()

        await client.fetch_device_information()

        if authentication_code is None:
            logging.info("No authentication code, skipping authentication")
        else:
            await client.authenticate(authentication_code=authentication_code)

        sensors = await client.fetch_sensor_data()
        logging.info(f"Status: {sensors.as_dict()}")

        boost = await client.fetch_boost()
        logging.info(f"Boost: {boost}")

        constant_speed = await client.fetch_constant_speed()
        logging.info(f"Constant speed: {constant_speed}")

        humidity = await client.fetch_humidity()
        logging.info(f"Humidity: {humidity}")

        light_and_voc = await client.fetch_light_and_voc()
        logging.info(f"Light and VOC: {light_and_voc}")

        pause = await client.fetch_pause()
        logging.info(f"Pause: {pause}")

        timer = await client.fetch_timer()
        logging.info(f"Timer: {timer}")
    except Exception as e:
        await client.disconnect()
        logging.error(e)


if __name__ == "__main__":
    asyncio.run(main())
