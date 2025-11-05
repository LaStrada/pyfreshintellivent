"""Tests for device module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from pyfreshintellivent.device import (
    AuthenticationError,
    DisconnectedError,
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventError,
    FreshIntelliventTimeoutError,
    UnsupportedDeviceError,
)
from pyfreshintellivent.models import FreshIntelliventDevice


@pytest.fixture
def ble_device():
    """Create a mock BLE device."""
    device = Mock(spec=BLEDevice)
    device.address = "AA:BB:CC:DD:EE:FF"
    device.name = "FreshSky"
    return device


@pytest.fixture
def mock_client():
    """Create a mock BleakClient."""
    client = AsyncMock()
    client.address = "AA:BB:CC:DD:EE:FF"
    client.is_connected = True
    return client


class TestExceptions:
    """Test exception classes."""

    def test_fresh_intellivent_error(self):
        """Test base exception."""
        exc = FreshIntelliventError("test error")
        assert str(exc) == "test error"
        assert isinstance(exc, Exception)

    def test_disconnected_error(self):
        """Test disconnected error."""
        exc = DisconnectedError("disconnected")
        assert str(exc) == "disconnected"
        assert isinstance(exc, FreshIntelliventError)

    def test_authentication_error(self):
        """Test authentication error."""
        exc = AuthenticationError("auth failed")
        assert str(exc) == "auth failed"
        assert isinstance(exc, FreshIntelliventError)

    def test_unsupported_device_error(self):
        """Test unsupported device error."""
        exc = UnsupportedDeviceError("not supported")
        assert str(exc) == "not supported"
        assert isinstance(exc, FreshIntelliventError)

    def test_timeout_error(self):
        """Test timeout error."""
        exc = FreshIntelliventTimeoutError("timeout")
        assert str(exc) == "timeout"
        assert isinstance(exc, FreshIntelliventError)


class TestFreshIntelliventBluetoothDeviceData:
    """Test FreshIntelliventBluetoothDeviceData class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        parser = FreshIntelliventBluetoothDeviceData()
        assert parser.max_attempts == 3
        assert parser.authentication_code is None
        assert parser.logger is not None

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        import logging

        logger = logging.getLogger("test")
        parser = FreshIntelliventBluetoothDeviceData(
            logger=logger, max_attempts=5, authentication_code="1234"
        )
        assert parser.max_attempts == 5
        assert parser.authentication_code == "1234"
        assert parser.logger == logger

    def test_handle_disconnect(self):
        """Test disconnect handler."""
        parser = FreshIntelliventBluetoothDeviceData()
        mock_client = Mock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"

        loop = asyncio.new_event_loop()
        disconnect_future = loop.create_future()

        parser._handle_disconnect(disconnect_future, mock_client)

        assert disconnect_future.done()
        assert disconnect_future.result() is True
        loop.close()

    def test_handle_disconnect_already_done(self):
        """Test disconnect handler when future is already done."""
        parser = FreshIntelliventBluetoothDeviceData()
        mock_client = Mock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"

        loop = asyncio.new_event_loop()
        disconnect_future = loop.create_future()
        disconnect_future.set_result(True)

        # Should not raise even if future is already done
        parser._handle_disconnect(disconnect_future, mock_client)

        assert disconnect_future.done()
        loop.close()

    @pytest.mark.asyncio
    async def test_update_device_retry_on_disconnect(self, ble_device):
        """Test that update_device retries on disconnect."""
        parser = FreshIntelliventBluetoothDeviceData(max_attempts=3)

        with patch.object(parser, "_update_device") as mock_update:
            # Fail twice, succeed on third attempt
            mock_update.side_effect = [
                DisconnectedError("test1"),
                DisconnectedError("test2"),
                FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF"),
            ]

            result = await parser.update_device(ble_device)

            assert isinstance(result, FreshIntelliventDevice)
            assert mock_update.call_count == 3

    @pytest.mark.asyncio
    async def test_update_device_retry_on_bleak_error(self, ble_device):
        """Test that update_device retries on BleakError."""
        parser = FreshIntelliventBluetoothDeviceData(max_attempts=2)

        with patch.object(parser, "_update_device") as mock_update:
            # Fail once, succeed on second attempt
            mock_update.side_effect = [
                BleakError("test"),
                FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF"),
            ]

            result = await parser.update_device(ble_device)

            assert isinstance(result, FreshIntelliventDevice)
            assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_update_device_fails_after_max_attempts_disconnect(self, ble_device):
        """Test that update_device fails after max attempts on disconnect."""
        parser = FreshIntelliventBluetoothDeviceData(max_attempts=2)

        with patch.object(parser, "_update_device") as mock_update:
            mock_update.side_effect = DisconnectedError("test")

            with pytest.raises(DisconnectedError):
                await parser.update_device(ble_device)

            assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_update_device_fails_after_max_attempts_bleak_error(self, ble_device):
        """Test that update_device fails after max attempts on BleakError."""
        parser = FreshIntelliventBluetoothDeviceData(max_attempts=2)

        with patch.object(parser, "_update_device") as mock_update:
            mock_update.side_effect = BleakError("test")

            with pytest.raises(BleakError):
                await parser.update_device(ble_device)

            assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_without_code(self, mock_client):
        """Test authenticate without authentication code."""
        parser = FreshIntelliventBluetoothDeviceData()

        # Should do nothing when no auth code provided
        await parser.authenticate(mock_client)

        mock_client.write_gatt_char.assert_not_called()

    @pytest.mark.asyncio
    async def test_authenticate_with_code(self, mock_client):
        """Test authenticate with authentication code."""
        parser = FreshIntelliventBluetoothDeviceData(authentication_code="1234")

        await parser.authenticate(mock_client)

        # Should write auth code
        mock_client.write_gatt_char.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, mock_client):
        """Test authenticate failure."""
        parser = FreshIntelliventBluetoothDeviceData(authentication_code="1234")

        # Mock write to raise error
        mock_client.write_gatt_char.side_effect = BleakError("auth failed")

        with pytest.raises(AuthenticationError):
            await parser.authenticate(mock_client)


class TestDeviceDataReading:
    """Test device data reading methods."""

    @pytest.mark.asyncio
    async def test_get_device_info(self, mock_client):
        """Test reading device info."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # Mock characteristic reads - order: name, fw, hw, sw, mfr
        mock_client.read_gatt_char.side_effect = [
            b"FreshSky",  # Device name
            b"3.0",  # FW version
            b"1.0",  # HW version
            b"2.0",  # SW version
            b"Manufacturer",  # Manufacturer
        ]

        await parser.get_device_info(mock_client, device)

        assert device.name == "FreshSky"
        assert device.info.hw_version == "1.0"
        assert device.info.sw_version == "2.0"
        assert device.info.fw_version == "3.0"
        assert device.info.manufacturer == "Manufacturer"

    @pytest.mark.asyncio
    async def test_get_device_info_partial(self, mock_client):
        """Test reading device info with some missing values."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # Mock some reads to fail
        mock_client.read_gatt_char.side_effect = BleakError("not found")

        # Should not raise, just leave None for missing values
        await parser.get_device_info(mock_client, device)

        assert device.name is None
        assert device.info.hw_version is None

    @pytest.mark.asyncio
    async def test_get_sensor_data(self, mock_client):
        """Test reading sensor data."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # Mock sensor data read
        mock_client.read_gatt_char.return_value = bytearray.fromhex(
            "01003702E60Abd01D204040B001c00"
        )

        await parser.get_sensor_data(mock_client, device)

        assert device.sensors.status is True
        assert device.sensors.temperature == 27.9
        assert device.sensors.rpm == 1234

    @pytest.mark.asyncio
    async def test_get_sensor_data_error(self, mock_client):
        """Test reading sensor data with error (should not raise)."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # Mock read to raise error
        mock_client.read_gatt_char.side_effect = BleakError("characteristic not found")

        # Should not raise, just log debug message
        await parser.get_sensor_data(mock_client, device)

        # Sensors should remain at default values
        assert device.sensors is not None


class TestUpdateDeviceInternal:
    """Test internal _update_device method."""

    @pytest.mark.asyncio
    async def test_update_device_successful(self, ble_device):
        """Test successful device update through _update_device."""
        parser = FreshIntelliventBluetoothDeviceData()

        with patch(
            "pyfreshintellivent.device.establish_connection"
        ) as mock_establish, patch.object(
            parser, "get_device_info"
        ) as mock_info, patch.object(
            parser, "get_sensor_data"
        ) as mock_sensor, patch.object(
            parser, "get_mode_settings"
        ) as mock_modes:

            mock_client = AsyncMock()
            mock_client.address = "AA:BB:CC:DD:EE:FF"
            mock_client.disconnect = AsyncMock()
            mock_establish.return_value = mock_client

            result = await parser._update_device(ble_device)

            assert isinstance(result, FreshIntelliventDevice)
            assert result.address == "AA:BB:CC:DD:EE:FF"
            mock_info.assert_called_once()
            mock_sensor.assert_called_once()
            mock_modes.assert_called_once()
            mock_client.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_update_device_with_authentication(self, ble_device):
        """Test device update with authentication."""
        parser = FreshIntelliventBluetoothDeviceData(authentication_code="1234")

        with patch(
            "pyfreshintellivent.device.establish_connection"
        ) as mock_establish, patch.object(
            parser, "authenticate"
        ) as mock_auth, patch.object(
            parser, "get_device_info"
        ) as mock_info, patch.object(
            parser, "get_sensor_data"
        ) as mock_sensor, patch.object(
            parser, "get_mode_settings"
        ) as mock_modes:

            mock_client = AsyncMock()
            mock_client.address = "AA:BB:CC:DD:EE:FF"
            mock_client.disconnect = AsyncMock()
            mock_establish.return_value = mock_client

            result = await parser._update_device(ble_device)

            assert isinstance(result, FreshIntelliventDevice)
            mock_auth.assert_called_once_with(mock_client)
            mock_info.assert_called_once()
            mock_sensor.assert_called_once()
            mock_modes.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_device_clears_cache_on_not_found(self, ble_device):
        """Test that characteristic cache is cleared on not found error."""
        parser = FreshIntelliventBluetoothDeviceData()

        with patch(
            "pyfreshintellivent.device.establish_connection"
        ) as mock_establish, patch.object(
            parser, "get_device_info"
        ) as mock_info:

            mock_client = AsyncMock()
            mock_client.address = "AA:BB:CC:DD:EE:FF"
            mock_client.clear_cache = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_establish.return_value = mock_client

            # Raise a "not found" error
            mock_info.side_effect = BleakError("characteristic not found")

            with pytest.raises(BleakError):
                await parser._update_device(ble_device)

            mock_client.clear_cache.assert_called_once()
            mock_client.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_update_device_disconnects_on_unsupported_device(self, ble_device):
        """Test that device is disconnected on unsupported device error."""
        parser = FreshIntelliventBluetoothDeviceData()

        with patch(
            "pyfreshintellivent.device.establish_connection"
        ) as mock_establish, patch.object(
            parser, "get_device_info"
        ) as mock_info:

            mock_client = AsyncMock()
            mock_client.address = "AA:BB:CC:DD:EE:FF"
            mock_client.disconnect = AsyncMock()
            mock_establish.return_value = mock_client

            # Raise unsupported device error
            mock_info.side_effect = UnsupportedDeviceError("not supported")

            with pytest.raises(UnsupportedDeviceError):
                await parser._update_device(ble_device)

            mock_client.disconnect.assert_called()

    @pytest.mark.asyncio
    async def test_update_device_always_disconnects(self, ble_device):
        """Test that device is always disconnected even on error."""
        parser = FreshIntelliventBluetoothDeviceData()

        with patch(
            "pyfreshintellivent.device.establish_connection"
        ) as mock_establish, patch.object(
            parser, "get_device_info"
        ) as mock_info:

            mock_client = AsyncMock()
            mock_client.address = "AA:BB:CC:DD:EE:FF"
            mock_client.disconnect = AsyncMock()
            mock_establish.return_value = mock_client

            # Raise a generic error
            mock_info.side_effect = Exception("unexpected error")

            with pytest.raises(Exception):
                await parser._update_device(ble_device)

            # Should still disconnect
            mock_client.disconnect.assert_called()


class TestGetModeSettings:
    """Test get_mode_settings method."""

    @pytest.mark.asyncio
    async def test_get_humidity_mode(self, mock_client):
        """Test reading humidity mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # Mock humidity mode data (4 bytes: enabled, detection, rpm LSB, rpm MSB)
        # All 7 modes are read in sequence
        mock_client.read_gatt_char.side_effect = [
            bytearray.fromhex("0102F401"),  # Humidity
            BleakError("not found"),  # Light/VOC
            BleakError("not found"),  # Constant speed
            BleakError("not found"),  # Timer
            BleakError("not found"),  # Airing
            BleakError("not found"),  # Pause
            BleakError("not found"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.humidity is not None
        assert device.modes.humidity.enabled is True
        assert device.modes.humidity.rpm == 500

    @pytest.mark.asyncio
    async def test_get_light_and_voc_mode(self, mock_client):
        """Test reading light and VOC mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # 4 bytes: light enabled, light detection, voc enabled, voc detection
        mock_client.read_gatt_char.side_effect = [
            BleakError("not found"),  # Humidity
            bytearray.fromhex("01010101"),  # Light and VOC
            BleakError("not found"),  # Constant speed
            BleakError("not found"),  # Timer
            BleakError("not found"),  # Airing
            BleakError("not found"),  # Pause
            BleakError("not found"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.light_and_voc is not None
        assert device.modes.light_and_voc.light.enabled is True
        assert device.modes.light_and_voc.voc.enabled is True

    @pytest.mark.asyncio
    async def test_get_constant_speed_mode(self, mock_client):
        """Test reading constant speed mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # 3 bytes: enabled, rpm LSB, rpm MSB
        mock_client.read_gatt_char.side_effect = [
            BleakError("not found"),  # Humidity
            BleakError("not found"),  # Light/VOC
            bytearray.fromhex("013905"),  # Constant speed (1337 rpm)
            BleakError("not found"),  # Timer
            BleakError("not found"),  # Airing
            BleakError("not found"),  # Pause
            BleakError("not found"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.constant_speed is not None
        assert device.modes.constant_speed.enabled is True
        assert device.modes.constant_speed.rpm == 1337

    @pytest.mark.asyncio
    async def test_get_timer_mode(self, mock_client):
        """Test reading timer mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # 5 bytes: delay enabled, delay minutes, minutes, rpm LSB, rpm MSB
        mock_client.read_gatt_char.side_effect = [
            BleakError("not found"),  # Humidity
            BleakError("not found"),  # Light/VOC
            BleakError("not found"),  # Constant speed
            bytearray.fromhex("050102E803"),  # Timer (delay: true/5min, 2min, 1000rpm)
            BleakError("not found"),  # Airing
            BleakError("not found"),  # Pause
            BleakError("not found"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.timer is not None
        assert device.modes.timer.delay.enabled is True
        assert device.modes.timer.delay.minutes == 2
        assert device.modes.timer.minutes == 5
        assert device.modes.timer.rpm == 1000

    @pytest.mark.asyncio
    async def test_get_airing_mode(self, mock_client):
        """Test reading airing mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # 5 bytes: enabled, minutes, rpm LSB, rpm MSB, extra byte
        mock_client.read_gatt_char.side_effect = [
            BleakError("not found"),  # Humidity
            BleakError("not found"),  # Light/VOC
            BleakError("not found"),  # Constant speed
            BleakError("not found"),  # Timer
            bytearray.fromhex("01261EE803"),  # Airing (38 min, 1000 rpm)
            BleakError("not found"),  # Pause
            BleakError("not found"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.airing is not None
        assert device.modes.airing.enabled is True
        assert device.modes.airing.minutes == 30
        assert device.modes.airing.rpm == 1000

    @pytest.mark.asyncio
    async def test_get_pause_mode(self, mock_client):
        """Test reading pause mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # 2 bytes: enabled, minutes
        mock_client.read_gatt_char.side_effect = [
            BleakError("not found"),  # Humidity
            BleakError("not found"),  # Light/VOC
            BleakError("not found"),  # Constant speed
            BleakError("not found"),  # Timer
            BleakError("not found"),  # Airing
            bytearray.fromhex("010A"),  # Pause (10 min)
            BleakError("not found"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.pause is not None
        assert device.modes.pause.enabled is True
        assert device.modes.pause.minutes == 10

    @pytest.mark.asyncio
    async def test_get_boost_mode(self, mock_client):
        """Test reading boost mode."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # 5 bytes: enabled, seconds LSB, seconds MSB, rpm LSB, rpm MSB
        mock_client.read_gatt_char.side_effect = [
            BleakError("not found"),  # Humidity
            BleakError("not found"),  # Light/VOC
            BleakError("not found"),  # Constant speed
            BleakError("not found"),  # Timer
            BleakError("not found"),  # Airing
            BleakError("not found"),  # Pause
            bytearray.fromhex("0160095802"),  # Boost (600 sec, 2400 rpm)
        ]

        await parser.get_mode_settings(mock_client, device)

        assert device.modes.boost is not None
        assert device.modes.boost.enabled is True
        assert device.modes.boost.seconds == 600
        assert device.modes.boost.rpm == 2400

    @pytest.mark.asyncio
    async def test_get_all_modes_success(self, mock_client):
        """Test reading all modes successfully."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # All modes return valid data
        mock_client.read_gatt_char.side_effect = [
            bytearray.fromhex("0102F401"),  # Humidity
            bytearray.fromhex("01010101"),  # Light and VOC
            bytearray.fromhex("013905"),  # Constant speed
            bytearray.fromhex("050102E803"),  # Timer
            bytearray.fromhex("01261EE803"),  # Airing
            bytearray.fromhex("010A"),  # Pause
            bytearray.fromhex("0160095802"),  # Boost
        ]

        await parser.get_mode_settings(mock_client, device)

        # Verify all modes were read
        assert device.modes.humidity is not None
        assert device.modes.light_and_voc is not None
        assert device.modes.constant_speed is not None
        assert device.modes.timer is not None
        assert device.modes.airing is not None
        assert device.modes.pause is not None
        assert device.modes.boost is not None

    @pytest.mark.asyncio
    async def test_get_modes_all_fail(self, mock_client):
        """Test reading modes when all fail (should not raise)."""
        parser = FreshIntelliventBluetoothDeviceData()
        device = FreshIntelliventDevice(address="AA:BB:CC:DD:EE:FF")

        # All reads fail
        mock_client.read_gatt_char.side_effect = BleakError("not found")

        # Should not raise, just log debug messages
        await parser.get_mode_settings(mock_client, device)

        # All modes should remain None
        assert device.modes.humidity is None
        assert device.modes.light_and_voc is None
        assert device.modes.constant_speed is None
        assert device.modes.timer is None
        assert device.modes.airing is None
        assert device.modes.pause is None
        assert device.modes.boost is None
