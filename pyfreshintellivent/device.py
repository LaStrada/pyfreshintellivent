"""Modern device reader with proper connection lifecycle management."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from uuid import UUID

from async_interrupt import interrupt
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from . import characteristics
from . import helpers as h
from .connection import ClientWithCleanup, ConnectionState, disconnect
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
from .exceptions import (
    AuthenticationError,
    ConnectionCleanupError,
    DisconnectedError,
    FreshIntelliventError,
    FreshIntelliventTimeoutError,
    UnsupportedDeviceError,
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

__all__ = [
    "AuthenticationError",
    "ConnectionCleanupError",
    "DisconnectedError",
    "FreshIntelliventBluetoothDeviceData",
    "FreshIntelliventDevice",
    "FreshIntelliventError",
    "FreshIntelliventTimeoutError",
    "UnsupportedDeviceError",
]


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
        if (
            isinstance(max_attempts, bool)
            or not isinstance(max_attempts, int)
            or max_attempts < 1
        ):
            raise ValueError("max_attempts must be a positive integer")
        self._update_lock = asyncio.Lock()
        self.logger = logger or logging.getLogger(__name__)
        self.max_attempts = max_attempts
        self.parser = SkyModeParser()
        self.authentication_code = authentication_code

    @property
    def authentication_code(self) -> bytes | str | None:
        """Return the configured authentication key."""
        return self._authentication_code

    @authentication_code.setter
    def authentication_code(self, value: bytes | bytearray | str | None) -> None:
        """Set the key for the next connection attempt; None selects anonymous reads."""
        if value is None:
            self._authentication_code: bytes | str | None = None
            return
        validated = h.validated_authentication_code(value)
        self._authentication_code = (
            value if isinstance(value, str) else bytes(validated)
        )

    def _handle_disconnect(
        self,
        disconnect_future: asyncio.Future[bool],
        address: str,
        _client: BleakClient,
    ) -> None:
        """Signal disconnect without accessing a potentially torn-down backend."""
        self.logger.debug("Disconnected from %s", address)
        if not disconnect_future.done():
            disconnect_future.set_result(True)

    async def update_device(self, ble_device: BLEDevice) -> FreshIntelliventDevice:
        """Connect to device, read all data, and disconnect.

        This method handles the complete lifecycle: connect, authenticate (if needed),
        read all device information and sensor data, then attempt bounded disconnect,
        including after errors and cancellation.
        A failed disconnect is reported; physical radio cleanup is not guaranteed.

        Args:
            ble_device: The BLE device to connect to

        Returns:
            FreshIntelliventDevice with all available data

        Raises:
            DisconnectedError: If device disconnects unexpectedly
            BleakError: If connection or communication fails after retries
            UnsupportedDeviceError: If device is not supported
        """
        async with self._update_lock:
            attempt = 0
            while True:
                try:
                    return await self._update_device(ble_device)
                except (
                    DisconnectedError,
                    FreshIntelliventTimeoutError,
                    BleakError,
                ) as err:
                    if attempt + 1 == self.max_attempts:
                        raise
                    await self._sleep_before_retry(ble_device, attempt, err)
                    attempt += 1

    async def pair_device(self, ble_device: BLEDevice) -> bytes:
        """Read a pairing key; retain it only after a successful read and disconnect."""
        async with self._update_lock:
            await self._update_device(ble_device, pairing=True)
            assert self.authentication_code is not None
            return bytes(h.validated_authentication_code(self.authentication_code))

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
            type(err).__name__,
            delay,
        )
        await asyncio.sleep(delay)

    async def _connect_device(
        self, ble_device: BLEDevice, disconnect_future: asyncio.Future[bool]
    ) -> BleakClientWithServiceCache:
        """Establish a connection without retrying after uncertain cleanup."""
        connection_state = ConnectionState()
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                client: BleakClientWithServiceCache = await establish_connection(
                    ClientWithCleanup,
                    ble_device,
                    ble_device.address,
                    disconnected_callback=partial(
                        self._handle_disconnect, disconnect_future, ble_device.address
                    ),
                    connection_state=connection_state,
                )
        except Exception as err:
            # Cancellation stays cancellation until the owning timeout converts it.
            # Cleanup failure then takes precedence over a retryable timeout/error.
            if connection_state.cleanup_error is not None:
                raise ConnectionCleanupError(
                    "Failed to close partial connection"
                ) from connection_state.cleanup_error
            if isinstance(err, TimeoutError):
                raise FreshIntelliventTimeoutError(
                    f"Timed out connecting to {ble_device.address}"
                ) from err
            raise
        return client

    async def _update_device(
        self, ble_device: BLEDevice, *, pairing: bool = False
    ) -> FreshIntelliventDevice:
        """Internal method to connect and read device data."""
        authentication_code = self.authentication_code
        device = FreshIntelliventDevice(address=ble_device.address)
        loop = asyncio.get_running_loop()
        disconnect_future: asyncio.Future[bool] = loop.create_future()
        client = await self._connect_device(ble_device, disconnect_future)
        pairing_key: bytearray | None = None
        primary_error: BaseException | None = None
        try:
            async with (
                interrupt(
                    disconnect_future,
                    DisconnectedError,
                    f"Disconnected from {ble_device.address}",
                ),
                asyncio.timeout(UPDATE_TIMEOUT),
            ):
                if pairing:
                    pairing_key = h.validated_authentication_code(
                        await client.read_gatt_char(characteristics.AUTH)
                    )
                    await self.authenticate(client, authentication_code=pairing_key)
                elif authentication_code is not None:
                    await self.authenticate(
                        client, authentication_code=authentication_code
                    )

                # Read device information
                await self.get_device_info(client, device, raise_on_not_found=True)

                # Read sensor data
                await self.get_sensor_data(client, device, raise_on_not_found=True)

                # Read mode settings
                await self.get_mode_settings(client, device, raise_on_not_found=True)

        except BaseException as err:
            primary_error = err
            if isinstance(err, TimeoutError):
                raise FreshIntelliventTimeoutError(
                    f"Timed out updating device {ble_device.address}"
                ) from err
            if isinstance(err, BleakError) and "not found" in str(err):
                try:
                    async with asyncio.timeout(UPDATE_TIMEOUT):
                        await client.clear_cache()
                # Backend errors must not replace the original failed read.
                # pylint: disable-next=broad-exception-caught
                except Exception as cache_error:
                    self.logger.debug(
                        "Cache cleanup failed (%s)", type(cache_error).__name__
                    )
            raise
        finally:
            try:
                await disconnect(client)
            except Exception as cleanup_error:  # pylint: disable=broad-exception-caught
                if primary_error is None:
                    raise ConnectionCleanupError(
                        "Failed to disconnect after update"
                    ) from cleanup_error
                if isinstance(
                    primary_error, (BleakError, DisconnectedError, TimeoutError)
                ):
                    raise ConnectionCleanupError(
                        "Failed to disconnect after failed read"
                    ) from primary_error
                self.logger.warning(
                    "Disconnect after failed update failed (%s)",
                    type(cleanup_error).__name__,
                )

        if pairing_key is not None:
            self.authentication_code = bytes(pairing_key)
        return device

    async def authenticate(
        self,
        client: BleakClient,
        *,
        authentication_code: bytes | bytearray | str | None = None,
    ) -> None:
        """Authenticate with the device using the provided authentication code."""
        code = (
            self.authentication_code
            if authentication_code is None
            else authentication_code
        )
        if code is None:
            return

        auth_data = h.validated_authentication_code(code)
        await client.write_gatt_char(characteristics.AUTH, auth_data, response=True)
        await asyncio.sleep(1)
        confirmation = await client.read_gatt_char(characteristics.AUTH_CONFIRMATION)
        if not confirmation or confirmation[0] != 1:
            raise AuthenticationError("Device rejected authentication")
        self.logger.debug("Authentication confirmed")

    async def _read_characteristic(
        self, client: BleakClient, characteristic: UUID, strict: bool
    ) -> bytearray | None:
        """Read a characteristic, optionally allowing incomplete diagnostic reads."""
        try:
            return await client.read_gatt_char(characteristic)
        except BleakError as err:
            if strict:
                raise
            self.logger.debug(
                "Could not read %s (%s)", characteristic, type(err).__name__
            )
            return None

    async def get_device_info(
        self,
        client: BleakClient,
        device: FreshIntelliventDevice,
        raise_on_not_found: bool = False,
    ) -> None:
        """Read device metadata; strict snapshots propagate every transport error."""
        data = await self._read_characteristic(
            client, characteristics.DEVICE_NAME, raise_on_not_found
        )
        if data is not None:
            device.name = data.decode("utf-8").rstrip("\0")
        for field, characteristic in (
            ("model_number", characteristics.MODEL_NUMBER),
            ("fw_version", characteristics.FIRMWARE_VERSION),
            ("hw_version", characteristics.HARDWARE_VERSION),
            ("sw_version", characteristics.SOFTWARE_VERSION),
            ("manufacturer", characteristics.MANUFACTURER_NAME),
        ):
            data = await self._read_characteristic(
                client, characteristic, raise_on_not_found
            )
            if data is not None:
                setattr(device.info, field, data.decode("utf-8").rstrip("\0"))

    async def get_sensor_data(
        self,
        client: BleakClient,
        device: FreshIntelliventDevice,
        raise_on_not_found: bool = False,
    ) -> None:
        """Read status, propagating all transport errors for strict snapshots."""
        data = await self._read_characteristic(
            client, characteristics.DEVICE_STATUS, raise_on_not_found
        )
        if data is not None:
            device.sensors = SensorData.from_bytes(data)

    async def get_mode_settings(
        self,
        client: BleakClient,
        device: FreshIntelliventDevice,
        raise_on_not_found: bool = False,
    ) -> None:
        """Read all mode settings from the device."""
        data = await self._read_characteristic(
            client, characteristics.HUMIDITY, raise_on_not_found
        )
        if data is not None:
            parsed = self.parser.humidity_read(data)
            device.modes.humidity = HumidityMode(
                enabled=bool(parsed[KEY_ENABLED]),
                detection=str(parsed[KEY_DETECTION]),
                detection_raw=int(parsed[KEY_DETECTION_RAW]),
                rpm=int(parsed[KEY_RPM]),
            )

        data = await self._read_characteristic(
            client, characteristics.LIGHT_VOC, raise_on_not_found
        )
        if data is not None:
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

        data = await self._read_characteristic(
            client, characteristics.CONSTANT_SPEED, raise_on_not_found
        )
        if data is not None:
            parsed = self.parser.constant_speed_read(data)  # type: ignore[assignment]
            device.modes.constant_speed = ConstantSpeedMode(
                enabled=bool(parsed[KEY_ENABLED]),
                rpm=int(parsed[KEY_RPM]),
            )

        data = await self._read_characteristic(
            client, characteristics.TIMER, raise_on_not_found
        )
        if data is not None:
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

        data = await self._read_characteristic(
            client, characteristics.AIRING, raise_on_not_found
        )
        if data is not None:
            parsed = self.parser.airing_read(data)  # type: ignore[assignment]
            device.modes.airing = AiringMode(
                cycle_period=int(parsed["cycle_period"]),
                enabled=bool(parsed[KEY_ENABLED]),
                minutes=int(parsed[KEY_MINUTES]),
                rpm=int(parsed[KEY_RPM]),
            )

        data = await self._read_characteristic(
            client, characteristics.PAUSE, raise_on_not_found
        )
        if data is not None:
            parsed = self.parser.pause_read(data)  # type: ignore[assignment]
            device.modes.pause = PauseMode(
                enabled=bool(parsed[KEY_ENABLED]),
                minutes=int(parsed[KEY_MINUTES]),
            )

        data = await self._read_characteristic(
            client, characteristics.BOOST, raise_on_not_found
        )
        if data is not None:
            parsed = self.parser.boost_read(data)  # type: ignore[assignment]
            device.modes.boost = BoostMode(
                enabled=bool(parsed[KEY_ENABLED]),
                seconds=int(parsed[KEY_SECONDS]),
                rpm=int(parsed[KEY_RPM]),
            )
