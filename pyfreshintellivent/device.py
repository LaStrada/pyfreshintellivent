"""Modern device reader with proper connection lifecycle management."""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from functools import partial

from async_interrupt import interrupt
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from . import characteristics
from .consts import DEFAULT_MAX_UPDATE_ATTEMPTS, DEVICE_MODEL, UPDATE_TIMEOUT
from .models import DeviceModes, SensorData
from .parser import SkyModeParser
from .sensors import SkySensors


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


# Device data model
@dataclasses.dataclass
class FreshIntelliventDevice:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Representation of a Fresh Intellivent device."""

    name: str | None = None
    address: str | None = None
    manufacturer: str | None = None
    model: str = DEVICE_MODEL
    hw_version: str | None = None
    sw_version: str | None = None
    fw_version: str | None = None
    sensors: SensorData = dataclasses.field(default_factory=SensorData)
    modes: DeviceModes = dataclasses.field(default_factory=DeviceModes)


class FreshIntelliventBluetoothDeviceData:
    """Data parser for Fresh Intellivent Sky devices with proper connection handling."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        max_attempts: int = DEFAULT_MAX_UPDATE_ATTEMPTS,
    ) -> None:
        """Initialize the parser.

        Args:
            logger: Optional logger instance
            max_attempts: Maximum number of connection retry attempts
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_attempts = max_attempts
        self.parser = SkyModeParser()

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
        for attempt in range(self.max_attempts):
            is_final_attempt = attempt == self.max_attempts - 1
            try:
                return await self._update_device(ble_device)
            except DisconnectedError:
                if is_final_attempt:
                    raise
                self.logger.debug(
                    "Unexpectedly disconnected from %s (attempt %d/%d)",
                    ble_device.address,
                    attempt + 1,
                    self.max_attempts,
                )
            except BleakError as err:
                if is_final_attempt:
                    raise
                self.logger.debug(
                    "Bleak error: %s (attempt %d/%d)",
                    err,
                    attempt + 1,
                    self.max_attempts,
                )
        raise RuntimeError("Should not reach this point")

    async def _update_device(self, ble_device: BLEDevice) -> FreshIntelliventDevice:
        """Internal method to connect and read device data."""
        device = FreshIntelliventDevice(address=ble_device.address)
        loop = asyncio.get_running_loop()
        disconnect_future = loop.create_future()

        client: BleakClientWithServiceCache = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            ble_device.address,
            disconnected_callback=partial(self._handle_disconnect, disconnect_future),
        )

        try:
            async with (
                interrupt(
                    disconnect_future,
                    DisconnectedError,
                    f"Disconnected from {client.address}",
                ),
                asyncio.timeout(UPDATE_TIMEOUT),
            ):
                # Read device information
                await self._get_device_info(client, device)

                # Read sensor data
                await self._get_sensor_data(client, device)

        except BleakError as err:
            if "not found" in str(err):
                # Clear the char cache since a char is likely missing
                await client.clear_cache()
            raise
        except UnsupportedDeviceError:
            await client.disconnect()
            raise
        finally:
            await client.disconnect()

        return device

    async def _get_device_info(
        self, client: BleakClient, device: FreshIntelliventDevice
    ) -> None:
        """Read device information characteristics."""
        try:
            name_bytes = await client.read_gatt_char(characteristics.DEVICE_NAME)
            device.name = (
                name_bytes.decode("utf-8").replace("\00", "").replace("\0", "")
            )
        except BleakError:
            self.logger.debug("Could not read device name")

        try:
            fw_bytes = await client.read_gatt_char(characteristics.FIRMWARE_VERSION)
            device.fw_version = fw_bytes.decode("utf-8")
        except BleakError:
            self.logger.debug("Could not read firmware version")

        try:
            hw_bytes = await client.read_gatt_char(characteristics.HARDWARE_VERSION)
            device.hw_version = hw_bytes.decode("utf-8")
        except BleakError:
            self.logger.debug("Could not read hardware version")

        try:
            sw_bytes = await client.read_gatt_char(characteristics.SOFTWARE_VERSION)
            device.sw_version = sw_bytes.decode("utf-8")
        except BleakError:
            self.logger.debug("Could not read software version")

        try:
            mfr_bytes = await client.read_gatt_char(characteristics.MANUFACTURER_NAME)
            device.manufacturer = mfr_bytes.decode("utf-8")
        except BleakError:
            self.logger.debug("Could not read manufacturer name")

    async def _get_sensor_data(
        self, client: BleakClient, device: FreshIntelliventDevice
    ) -> None:
        """Read sensor data from the device."""
        try:
            data = await client.read_gatt_char(characteristics.DEVICE_STATUS)
            sensors = SkySensors()
            sensors.parse_data(data)

            # Convert to typed model
            device.sensors = SensorData(
                status=sensors.status,
                mode=sensors.mode,
                mode_raw=sensors.mode_raw,
                temperature=sensors.temperature,
                temperature_avg=sensors.temperature_avg,
                rpm=sensors.rpm,
                humidity=sensors.humidity,
                authenticated=sensors.authenticated,
                unknowns=sensors.unknowns,
            )
        except BleakError as err:
            self.logger.debug("Could not read sensor data: %s", err)
