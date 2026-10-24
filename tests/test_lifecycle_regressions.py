"""Behavioral regressions for polling, cancellation, cleanup and input validation."""

import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from pyfreshintellivent.device import (
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventError,
)
from pyfreshintellivent.helpers import validated_authentication_code
from pyfreshintellivent.models import FreshIntelliventDevice


@pytest.mark.parametrize("attempts", [0, -1, True, 1.5, "3"])
def test_invalid_attempt_count(attempts):
    with pytest.raises(ValueError):
        FreshIntelliventBluetoothDeviceData(max_attempts=attempts)


@pytest.mark.parametrize(
    "code,error",
    [
        (None, TypeError),
        (12, TypeError),
        ("", ValueError),
        ("1234", ValueError),
        ("gggggggg", ValueError),
        ("12 34 56", ValueError),
        ("00000000", ValueError),
        (b"\0" * 4, ValueError),
        (b"123", ValueError),
    ],
)
def test_auth_code_rejects_invalid_without_echo(code, error):
    with pytest.raises(error):
        validated_authentication_code(code)


@pytest.mark.asyncio
async def test_concurrent_updates_are_serialized_and_waiter_can_cancel():
    reader = FreshIntelliventBluetoothDeviceData()
    first_entered = asyncio.Event()
    release = asyncio.Event()
    count = 0

    async def read(device):
        nonlocal count
        count += 1
        first_entered.set()
        await release.wait()
        return FreshIntelliventDevice(address=device.address)

    device = Mock(spec=BLEDevice, address="AA:BB:CC:DD:EE:FF")
    with patch.object(reader, "_update_device", side_effect=read) as update:
        first = asyncio.create_task(reader.update_device(device))
        tasks = [first]
        try:
            async with asyncio.timeout(5):
                await first_entered.wait()
                waiter = asyncio.create_task(reader.update_device(device))
                tasks.append(waiter)
                await asyncio.sleep(0)
                assert count == 1
                waiter.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await waiter
                release.set()
                await first
                await reader.update_device(device)
                assert update.await_count == 2
        finally:
            release.set()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_cancelled_poll_disconnects_before_next_update():
    reader = FreshIntelliventBluetoothDeviceData()
    entered = asyncio.Event()
    disconnected = asyncio.Event()
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")

    async def read(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    async def cleanup():
        disconnected.set()

    client.disconnect.side_effect = cleanup
    with (
        patch("pyfreshintellivent.device.establish_connection", return_value=client),
        patch.object(reader, "get_device_info", side_effect=read),
    ):
        task = asyncio.create_task(reader.update_device(Mock(address=client.address)))
        try:
            async with asyncio.timeout(5):
                await entered.wait()
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            assert disconnected.is_set()
            assert not reader._update_lock.locked()
            client.disconnect.assert_awaited_once()
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


@pytest.mark.asyncio
@pytest.mark.parametrize("primary", [None, ValueError("bad packet")])
async def test_disconnect_failure_preserves_primary_and_prevents_success(primary):
    reader = FreshIntelliventBluetoothDeviceData()
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.disconnect.side_effect = BleakError("disconnect failed")
    with (
        patch(
            "pyfreshintellivent.device.establish_connection", return_value=client
        ) as connect,
        patch.object(reader, "get_device_info", side_effect=primary),
        patch.object(reader, "get_sensor_data"),
        patch.object(reader, "get_mode_settings"),
    ):
        expected = type(primary) if primary else FreshIntelliventError
        with pytest.raises(expected):
            await reader.update_device(Mock(address=client.address))
        connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_cache_failure_preserves_read_failure():
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=1)
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    original = BleakError("characteristic not found")
    client.read_gatt_char.side_effect = original
    client.clear_cache.side_effect = RuntimeError("cache broken")
    with patch("pyfreshintellivent.device.establish_connection", return_value=client):
        with pytest.raises(BleakError) as raised:
            await reader.update_device(Mock(address=client.address))
        assert raised.value is original
        client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method", ["get_device_info", "get_sensor_data", "get_mode_settings"]
)
async def test_strict_snapshot_propagates_transport_errors(method):
    reader = FreshIntelliventBluetoothDeviceData()
    client = AsyncMock()
    client.read_gatt_char.side_effect = BleakError("link lost")
    with pytest.raises(BleakError, match="link lost"):
        await getattr(reader, method)(
            client, FreshIntelliventDevice(), raise_on_not_found=True
        )


@pytest.mark.asyncio
async def test_failed_disconnect_stops_retry_after_transport_error():
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=3)
    client = AsyncMock(address="AA:BB:CC:DD:EE:FF")
    client.disconnect.side_effect = BleakError("disconnect failed")
    client.read_gatt_char.side_effect = BleakError("read failed")
    with patch(
        "pyfreshintellivent.device.establish_connection", return_value=client
    ) as connect:
        with pytest.raises(
            FreshIntelliventError, match="Failed to disconnect"
        ) as raised:
            await reader.update_device(Mock(address=client.address))
        assert isinstance(raised.value.__cause__, BleakError)
        connect.assert_awaited_once()
