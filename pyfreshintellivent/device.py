"""Modern device reader with proper connection lifecycle management."""

from __future__ import annotations

import asyncio
import logging
from functools import partial

from async_interrupt import interrupt
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from . import characteristics
from . import helpers as h
from .consts import (
    DEFAULT_MAX_UPDATE_ATTEMPTS,
    KEY_DELAY,
    KEY_DETECTION,
    KEY_DETECTION_RAW,
    KEY_ENABLED,
    KEY_LIGHT,
    KEY_MINUTES,
    KEY_RPM,
    KEY_SECONDS,
    KEY_VOC,
    UPDATE_TIMEOUT,
)
from .models import (
    AiringMode,
    BoostMode,
    ConstantSpeedMode,
    DelaySettings,
    FreshIntelliventDevice,
    HumidityMode,
    LightAndVocMode,
    LightSettings,
    PauseMode,
    SensorData,
    TimerMode,
    VocSettings,
)
from .parser import SkyModeParser


# Exception classes
class FreshIntelliventError(Exception):
    """Base exception for Fresh Intellivent errors."""


class DisconnectedError(FreshIntelliventError):
    """Device disconnected unexpectedly."""


class AuthenticationError(FreshIntelliventError):
    """Authentication failed."""


class UnsupportedDeviceError(FreshIntelliventError):
    """Device is not supported."""


class FreshIntelliventTimeoutError(FreshIntelliventError):
    """Timeout exception for Fresh Intellivent errors."""


# Device data parser
class FreshIntelliventBluetoothDeviceData:
    """Data parser for Fresh Intellivent Sky devices with proper connection handling."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        max_attempts: int = DEFAULT_MAX_UPDATE_ATTEMPTS,
        authentication_code: bytes | bytearray | str | None = None,
    ) -> None:
        """Initialize the parser.

        Args:
            logger: Optional logger instance
            max_attempts: Maximum number of connection retry attempts
            authentication_code: Optional authentication code for protected devices
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_attempts = max_attempts
        self.parser = SkyModeParser()
        self.authentication_code = authentication_code

    def _handle_disconnect(
        self, disconnect_future: asyncio.Future[bool], client: BleakClient
    ) -> None:
        """Handle disconnect from device."""
        self.logger.debug("Disconnected from %s", client.address)
        if not disconnect_future.done():
            disconnect_future.set_result(True)

    async def update_device(self, ble_device: BLEDevice) -> FreshIntelliventDevice:
        """Connect to device, read all data, and disconnect.

        This method handles the complete lifecycle: connect, authenticate (if needed),
        read all device information and sensor data, then disconnect. The connection
        is guaranteed to be closed even if errors occur.

        Args:
            ble_device: The BLE device to connect to

        Returns:
            FreshIntelliventDevice with all available data

        Raises:
            DisconnectedError: If device disconnects unexpectedly
            BleakError: If connection or communication fails after retries
            UnsupportedDeviceError: If device is not supported
        """
        retryable = (DisconnectedError, FreshIntelliventTimeoutError, BleakError)
        for attempt in range(self.max_attempts):
            try:
                return await self._update_device(ble_device)
            except retryable as err:
                is_final_attempt = attempt == self.max_attempts - 1
                if is_final_attempt:
                    raise
                await self._sleep_before_retry(ble_device, attempt, err)
        raise RuntimeError("Should not reach this point")

    async def _sleep_before_retry(
        self, ble_device: BLEDevice, attempt: int, err: Exception
    ) -> None:
        """Sleep before retrying a failed update."""
        delay = 1.0
        self.logger.debug(
            "Attempt %d/%d to update %s failed (%s). Retrying in %.1fs",
            attempt + 1,
            self.max_attempts,
            ble_device.address,
            err,
            delay,
        )
        await asyncio.sleep(delay)

    async def _update_device(self, ble_device: BLEDevice) -> FreshIntelliventDevice:
        """Internal method to connect and read device data."""
        device = FreshIntelliventDevice(address=ble_device.address)
        loop = asyncio.get_running_loop()
        disconnect_future = loop.create_future()

        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                client: BleakClientWithServiceCache = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    ble_device.address,
                    disconnected_callback=partial(
                        self._handle_disconnect, disconnect_future
                    ),
                )
        except asyncio.TimeoutError as err:
            raise FreshIntelliventTimeoutError(
                f"Timed out connecting to {ble_device.address}"
            ) from err
        else:
            try:
                async with (
                    interrupt(
                        disconnect_future,
                        DisconnectedError,
                        f"Disconnected from {client.address}",
                    ),
                    asyncio.timeout(UPDATE_TIMEOUT),
                ):
                    # Authenticate if code provided
                    if self.authentication_code:
                        await self.authenticate(client)

                    # Read device information
                    await self.get_device_info(
                        client, device, raise_on_not_found=True
                    )

                    # Read sensor data
                    await self.get_sensor_data(
                        client, device, raise_on_not_found=True
                    )

                    # Read mode settings
                    await self.get_mode_settings(
                        client, device, raise_on_not_found=True
                    )

            except asyncio.TimeoutError as err:
                raise FreshIntelliventTimeoutError(
                    f"Timed out updating device {ble_device.address}"
                ) from err
            except BleakError as err:
                if "not found" in str(err):
                    # Clear the char cache since a char is likely missing
                    await client.clear_cache()
                raise
            except UnsupportedDeviceError:
                raise
            finally:
                await client.disconnect()

        return device

    async def authenticate(self, client: BleakClient) -> None:
        """Authenticate with the device using the provided authentication code."""
        if not self.authentication_code:
            return

        try:
            # Convert authentication code to bytearray
            auth_data = h.to_bytearray(self.authentication_code)

            # Write authentication code
            await client.write_gatt_char(characteristics.AUTH, auth_data, response=True)

            # Wait for authentication to process
            await asyncio.sleep(1)

            self.logger.debug("Authentication successful")
        except BleakError as err:
            self.logger.error("Authentication failed: %s", err)
            raise AuthenticationError(f"Failed to authenticate: {err}") from err

    async def get_device_info(
        self,
        client: BleakClient,
        device: FreshIntelliventDevice,
        raise_on_not_found: bool = False,
    ) -> None:
        """Read device information characteristics."""
        try:
            name_bytes = await client.read_gatt_char(characteristics.DEVICE_NAME)
            self.logger.debug("RAW DATA - DEVICE_NAME: %s", name_bytes.hex())
            device.name = (
                name_bytes.decode("utf-8").replace("\00", "").replace("\0", "")
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read device name")

        try:
            fw_bytes = await client.read_gatt_char(characteristics.FIRMWARE_VERSION)
            self.logger.debug("RAW DATA - FIRMWARE_VERSION: %s", fw_bytes.hex())
            device.info.fw_version = fw_bytes.decode("utf-8")
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read firmware version")

        try:
            hw_bytes = await client.read_gatt_char(characteristics.HARDWARE_VERSION)
            self.logger.debug("RAW DATA - HARDWARE_VERSION: %s", hw_bytes.hex())
            device.info.hw_version = hw_bytes.decode("utf-8")
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read hardware version")

        try:
            sw_bytes = await client.read_gatt_char(characteristics.SOFTWARE_VERSION)
            self.logger.debug("RAW DATA - SOFTWARE_VERSION: %s", sw_bytes.hex())
            device.info.sw_version = sw_bytes.decode("utf-8")
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read software version")

        try:
            mfr_bytes = await client.read_gatt_char(characteristics.MANUFACTURER_NAME)
            self.logger.debug("RAW DATA - MANUFACTURER_NAME: %s", mfr_bytes.hex())
            device.info.manufacturer = mfr_bytes.decode("utf-8")
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read manufacturer name")

    async def get_sensor_data(
        self,
        client: BleakClient,
        device: FreshIntelliventDevice,
        raise_on_not_found: bool = False,
    ) -> None:
        """Read sensor data from the device."""
        try:
            data = await client.read_gatt_char(characteristics.DEVICE_STATUS)
            self.logger.debug("RAW DATA - DEVICE_STATUS: %s", data.hex())
            device.sensors = SensorData.from_bytes(data)
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read sensor data: %s", err)

    async def get_mode_settings(
        self,
        client: BleakClient,
        device: FreshIntelliventDevice,
        raise_on_not_found: bool = False,
    ) -> None:
        """Read all mode settings from the device."""
        # Read humidity mode
        try:
            data = await client.read_gatt_char(characteristics.HUMIDITY)
            self.logger.debug("RAW DATA - HUMIDITY: %s", data.hex())
            parsed = self.parser.humidity_read(data)
            device.modes.humidity = HumidityMode(
                enabled=bool(parsed[KEY_ENABLED]),
                detection=str(parsed[KEY_DETECTION]),
                detection_raw=int(parsed[KEY_DETECTION_RAW]),
                rpm=int(parsed[KEY_RPM]),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read humidity mode: %s", err)

        # Read light and VOC mode
        try:
            data = await client.read_gatt_char(characteristics.LIGHT_VOC)
            self.logger.debug("RAW DATA - LIGHT_VOC: %s", data.hex())
            parsed = self.parser.light_and_voc_read(data)
            light_data = parsed[KEY_LIGHT]
            voc_data = parsed[KEY_VOC]
            device.modes.light_and_voc = LightAndVocMode(
                light=LightSettings(
                    enabled=bool(light_data[KEY_ENABLED]),  # type: ignore
                    detection=str(light_data[KEY_DETECTION]),  # type: ignore
                    detection_raw=int(light_data[KEY_DETECTION_RAW]),  # type: ignore
                ),
                voc=VocSettings(
                    enabled=bool(voc_data[KEY_ENABLED]),  # type: ignore
                    detection=str(voc_data[KEY_DETECTION]),  # type: ignore
                    detection_raw=int(voc_data[KEY_DETECTION_RAW]),  # type: ignore
                ),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read light and VOC mode: %s", err)

        # Read constant speed mode
        try:
            data = await client.read_gatt_char(characteristics.CONSTANT_SPEED)
            self.logger.debug("RAW DATA - CONSTANT_SPEED: %s", data.hex())
            parsed = self.parser.constant_speed_read(data)  # type: ignore[assignment]
            device.modes.constant_speed = ConstantSpeedMode(
                enabled=bool(parsed[KEY_ENABLED]),
                rpm=int(parsed[KEY_RPM]),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read constant speed mode: %s", err)

        # Read timer mode
        try:
            data = await client.read_gatt_char(characteristics.TIMER)
            self.logger.debug("RAW DATA - TIMER: %s", data.hex())
            parsed = self.parser.timer_read(data)
            delay_data = parsed[KEY_DELAY]
            device.modes.timer = TimerMode(
                delay=DelaySettings(
                    enabled=bool(delay_data[KEY_ENABLED]),  # type: ignore
                    minutes=int(delay_data[KEY_MINUTES]),  # type: ignore
                ),
                minutes=int(parsed[KEY_MINUTES]),
                rpm=int(parsed[KEY_RPM]),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read timer mode: %s", err)

        # Read airing mode
        try:
            data = await client.read_gatt_char(characteristics.AIRING)
            self.logger.debug("RAW DATA - AIRING: %s", data.hex())
            parsed = self.parser.airing_read(data)  # type: ignore[assignment]
            device.modes.airing = AiringMode(
                enabled=bool(parsed[KEY_ENABLED]),
                minutes=int(parsed[KEY_MINUTES]),
                rpm=int(parsed[KEY_RPM]),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read airing mode: %s", err)

        # Read pause mode
        try:
            data = await client.read_gatt_char(characteristics.PAUSE)
            self.logger.debug("RAW DATA - PAUSE: %s", data.hex())
            parsed = self.parser.pause_read(data)  # type: ignore[assignment]
            device.modes.pause = PauseMode(
                enabled=bool(parsed[KEY_ENABLED]),
                minutes=int(parsed[KEY_MINUTES]),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read pause mode: %s", err)

        # Read boost mode
        try:
            data = await client.read_gatt_char(characteristics.BOOST)
            self.logger.debug("RAW DATA - BOOST: %s", data.hex())
            parsed = self.parser.boost_read(data)  # type: ignore[assignment]
            device.modes.boost = BoostMode(
                enabled=bool(parsed[KEY_ENABLED]),
                seconds=int(parsed[KEY_SECONDS]),
                rpm=int(parsed[KEY_RPM]),
            )
        except BleakError as err:
            if raise_on_not_found and "not found" in str(err):
                raise
            self.logger.debug("Could not read boost mode: %s", err)
