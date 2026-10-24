"""Protocol checks independent of transport, including negative PIN replies."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak.exc import BleakError

from pyfreshintellivent import characteristics
from pyfreshintellivent.device import (
    AuthenticationError,
    FreshIntelliventBluetoothDeviceData,
)
from pyfreshintellivent.parser import SkyModeParser


@pytest.mark.asyncio
@pytest.mark.parametrize("reply", [b"", b"\x00", b"\x02", b"\xff"])
async def test_negative_pin_confirmation(reply):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code="12345678")
    client = AsyncMock()
    client.read_gatt_char.return_value = reply
    with patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(AuthenticationError, match="rejected"):
            await reader.authenticate(client)
    client.read_gatt_char.assert_awaited_once_with(characteristics.AUTH_CONFIRMATION)


@pytest.mark.asyncio
async def test_pin_confirmation_transport_failure():
    reader = FreshIntelliventBluetoothDeviceData(authentication_code="12345678")
    client = AsyncMock()
    client.read_gatt_char.side_effect = BleakError("failed")
    with patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(BleakError, match="failed"):
            await reader.authenticate(client)


@pytest.mark.parametrize("raw,level", [(1, "Low"), (2, "Medium"), (3, "High")])
def test_voc_golden_values_and_roundtrip(raw, level):
    parser = SkyModeParser()
    packet = bytes([1, 2, 1, raw])
    assert parser.light_and_voc_read(packet)["voc"]["detection"] == level
    assert parser.light_and_voc_write(True, "Medium", True, level) == packet


def test_unknown_detection_is_not_clamped_to_high():
    parser = SkyModeParser()
    result = parser.light_and_voc_read(bytes([1, 255, 1, 254]))
    assert result["light"]["detection"] == "Unknown"
    assert result["light"]["detection_raw"] == 255
    assert result["voc"]["detection"] == "Unknown"
    assert result["voc"]["detection_raw"] == 254


@pytest.mark.asyncio
@pytest.mark.parametrize("key", [b"\0" * 4, b"", b"123"])
async def test_pairing_requires_nonzero_four_byte_key(key):
    reader = FreshIntelliventBluetoothDeviceData()
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.read_gatt_char.return_value = key
    with patch("pyfreshintellivent.device.establish_connection", return_value=client):
        with pytest.raises(ValueError):
            await reader.pair_device(Mock(address=client.address))
    client.disconnect.assert_awaited_once()
    client.write_gatt_char.assert_not_awaited()
    assert reader.authentication_code is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        None,
        AuthenticationError(),
        ValueError("packet"),
        BleakError("read"),
        asyncio.CancelledError(),
    ],
)
async def test_pairing_only_retains_verified_key_after_success(failure):
    original_key = b"old!"
    new_key = b"new!"
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=original_key)
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.read_gatt_char.side_effect = [new_key, b"\x01"]
    with (
        patch("pyfreshintellivent.device.establish_connection", return_value=client),
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
        patch.object(reader, "get_device_info", side_effect=failure),
        patch.object(reader, "get_sensor_data"),
        patch.object(reader, "get_mode_settings"),
    ):
        if failure is None:
            result = await reader.pair_device(Mock(address=client.address))
            assert result == new_key
            assert reader.authentication_code == new_key
        else:
            with pytest.raises(type(failure)):
                await reader.pair_device(Mock(address=client.address))
            assert reader.authentication_code == original_key
    client.write_gatt_char.assert_awaited_once_with(
        characteristics.AUTH, bytearray(new_key), response=True
    )
    client.disconnect.assert_awaited_once()
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
async def test_pairing_rejected_confirmation_does_not_store_key():
    reader = FreshIntelliventBluetoothDeviceData()
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.read_gatt_char.side_effect = [b"new!", b"\x00"]
    with (
        patch("pyfreshintellivent.device.establish_connection", return_value=client),
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(AuthenticationError):
            await reader.pair_device(Mock(address=client.address))
    assert reader.authentication_code is None
    client.disconnect.assert_awaited_once()


def test_airing_preserves_nondefault_cycle_period():
    parser = SkyModeParser()
    packet = bytes.fromhex("011805b004")
    values = parser.airing_read(packet)
    assert values == {"enabled": True, "cycle_period": 24, "minutes": 5, "rpm": 1200}
    assert (
        parser.airing_write(
            values["enabled"],
            values["minutes"],
            values["rpm"],
            cycle_period=values["cycle_period"],
        )
        == packet
    )


@pytest.mark.asyncio
async def test_pairing_cleanup_failure_does_not_retain_key():
    reader = FreshIntelliventBluetoothDeviceData()
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.read_gatt_char.side_effect = [b"new!", b"\x01"]
    client.disconnect.side_effect = BleakError("cleanup failed")
    with (
        patch(
            "pyfreshintellivent.device.establish_connection", return_value=client
        ) as connect,
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
        patch.object(reader, "get_device_info"),
        patch.object(reader, "get_sensor_data"),
        patch.object(reader, "get_mode_settings"),
    ):
        from pyfreshintellivent.exceptions import ConnectionCleanupError

        with pytest.raises(ConnectionCleanupError):
            await reader.pair_device(Mock(address=client.address))
    assert reader.authentication_code is None
    connect.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["write_gatt_char", "read_gatt_char"])
async def test_auth_transport_failure_retries_after_cleanup(operation, caplog):
    """A lost auth packet must not tell HA to discard a valid key."""
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code="12345678", max_attempts=2
    )
    first = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    second = AsyncMock(address=first.address)
    second.read_gatt_char.return_value = b"\x01"
    getattr(first, operation).side_effect = BleakError("backend-sensitive-payload")
    clients = iter([first, second])

    async def connect(*args, **kwargs):
        client = next(clients)
        if client is second:
            first.disconnect.assert_awaited_once()
        return client

    with (
        caplog.at_level("DEBUG", logger="pyfreshintellivent.device"),
        patch("pyfreshintellivent.device.establish_connection", side_effect=connect),
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
        patch.object(reader, "get_device_info"),
        patch.object(reader, "get_sensor_data"),
        patch.object(reader, "get_mode_settings"),
    ):
        result = await reader.update_device(Mock(address=first.address))
    assert result.address == first.address
    first.disconnect.assert_awaited_once()
    second.disconnect.assert_awaited_once()
    assert reader.authentication_code == "12345678"
    assert "backend-sensitive-payload" not in caplog.text


@pytest.mark.asyncio
async def test_rejected_authentication_is_not_retried():
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code="12345678", max_attempts=3
    )
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.read_gatt_char.return_value = b"\x00"
    with (
        patch(
            "pyfreshintellivent.device.establish_connection", return_value=client
        ) as connect,
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(AuthenticationError):
            await reader.update_device(Mock(address=client.address))
    connect.assert_awaited_once()
    client.disconnect.assert_awaited_once()


@pytest.mark.parametrize("raw,level", [(1, "Low"), (2, "Medium"), (3, "High")])
@pytest.mark.parametrize("light_enabled,voc_enabled", [(False, True), (True, False)])
def test_light_golden_values_preserve_sibling_settings(
    raw, level, light_enabled, voc_enabled
):
    """Decoding and re-encoding must not silently alter the light threshold."""
    parser = SkyModeParser()
    packet = bytes([light_enabled, raw, voc_enabled, 2])
    values = parser.light_and_voc_read(packet)
    assert values["light"] == {
        "enabled": light_enabled,
        "detection": level,
        "detection_raw": raw,
    }
    assert values["voc"] == {
        "enabled": voc_enabled,
        "detection": "Medium",
        "detection_raw": 2,
    }
    assert (
        parser.light_and_voc_write(
            values["light"]["enabled"],
            values["light"]["detection"],
            values["voc"]["enabled"],
            values["voc"]["detection"],
        )
        == packet
    )
