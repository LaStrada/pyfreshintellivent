"""Exercise connection ownership and cancellation against asynchronous backends."""

import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock, patch

import pytest
from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache

from pyfreshintellivent.connection import ClientWithCleanup, disconnect
from pyfreshintellivent.exceptions import ConnectionCleanupError


@pytest.mark.asyncio
async def test_disconnect_waits_through_repeated_cancellation():
    entered = asyncio.Event()
    release = asyncio.Event()

    async def slow_disconnect():
        entered.set()
        await release.wait()

    client = AsyncMock()
    client.disconnect.side_effect = slow_disconnect
    task = asyncio.create_task(disconnect(client))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done()
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
        client.disconnect.assert_awaited_once()
    finally:
        release.set()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_disconnect_times_out():
    client = AsyncMock()
    client.disconnect.side_effect = lambda: None

    async def hang():
        await asyncio.Event().wait()

    client.disconnect.side_effect = hang
    with patch("pyfreshintellivent.connection.DISCONNECT_TIMEOUT", 0.001):
        with pytest.raises(TimeoutError):
            await disconnect(client)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error,expected",
    [
        (BleakError("transport"), BleakError),
        (asyncio.CancelledError(), ConnectionCleanupError),
    ],
)
async def test_disconnect_propagates_backend_failure(error, expected):
    client = AsyncMock()
    client.disconnect.side_effect = error
    with pytest.raises(expected):
        await disconnect(client)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cleanup_error", [BleakError("cleanup failed"), asyncio.CancelledError()]
)
async def test_cancelled_cleanup_retrieves_error_without_masking_cancel(cleanup_error):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def cleanup():
        entered.set()
        await release.wait()
        raise cleanup_error

    client = AsyncMock()
    client.disconnect.side_effect = cleanup
    task = asyncio.create_task(disconnect(client))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
            task.cancel()
            await asyncio.sleep(0)
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
    finally:
        release.set()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_client_success_does_not_disconnect():
    with patch.object(BleakClient, "__init__", return_value=None):
        client = ClientWithCleanup("AA:BB:CC:DD:EE:FF")
    with (
        patch.object(
            BleakClientWithServiceCache, "connect", new_callable=AsyncMock
        ) as connect,
        patch(
            "pyfreshintellivent.connection.disconnect", new_callable=AsyncMock
        ) as cleanup,
    ):
        await client.connect(timeout=5)
        connect.assert_awaited_once_with(timeout=5)
        cleanup.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", [BleakError("connect failed"), asyncio.CancelledError()]
)
@pytest.mark.parametrize("cleanup_error", [None, BleakError("cleanup failed")])
async def test_partial_connection_is_closed(error, cleanup_error):
    with patch.object(BleakClient, "__init__", return_value=None):
        client = ClientWithCleanup("AA:BB:CC:DD:EE:FF")
    with (
        patch.object(
            BleakClientWithServiceCache,
            "connect",
            new_callable=AsyncMock,
            side_effect=error,
        ),
        patch(
            "pyfreshintellivent.connection.disconnect",
            new_callable=AsyncMock,
            side_effect=cleanup_error,
        ) as cleanup,
    ):
        expected = (
            ConnectionCleanupError
            if cleanup_error is not None and isinstance(error, BleakError)
            else type(error)
        )
        with pytest.raises(expected):
            await client.connect()
        cleanup.assert_awaited_once_with(
            client, connection_state=client._connection_state
        )


@pytest.mark.asyncio
async def test_prior_consumed_cancellation_is_not_new_caller_cancellation():
    """An old cancellation count cannot hide a later backend cleanup failure."""
    client = AsyncMock()
    client.disconnect.side_effect = asyncio.CancelledError()

    async def run():
        task = asyncio.current_task()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(0)
        assert task.cancelling() == 1
        with pytest.raises(ConnectionCleanupError):
            await disconnect(client)
        assert task.cancelling() == 1

    task = asyncio.create_task(run())
    try:
        async with asyncio.timeout(5):
            await task
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    client.disconnect.assert_awaited_once()
