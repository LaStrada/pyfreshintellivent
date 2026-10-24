"""Exercise real connector retries and deadlines with isolated BLE backends."""

import asyncio
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from pyfreshintellivent import characteristics
from pyfreshintellivent.device import (
    DisconnectedError,
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventTimeoutError,
)
from pyfreshintellivent.exceptions import ConnectionCleanupError


@pytest.fixture
def transport():
    """Keep the connector and client lifecycle real, replacing only OS I/O."""
    device = BLEDevice("AA:BB:CC:DD:EE:FF", "Intellivent SKY", {})
    backends = [AsyncMock(address=device.address), AsyncMock(address=device.address)]
    callbacks = []
    packets = {
        characteristics.DEVICE_NAME: b"Intellivent SKY",
        characteristics.MODEL_NUMBER: b"40",
        characteristics.FIRMWARE_VERSION: b"3.0",
        characteristics.HARDWARE_VERSION: b"1.0",
        characteristics.SOFTWARE_VERSION: b"2.0",
        characteristics.MANUFACTURER_NAME: b"Fresh",
        characteristics.DEVICE_STATUS: bytes.fromhex("01003702e60abd01d204040b001c00"),
        characteristics.HUMIDITY: bytes.fromhex("0102f401"),
        characteristics.LIGHT_VOC: bytes.fromhex("01010101"),
        characteristics.CONSTANT_SPEED: bytes.fromhex("013905"),
        characteristics.TIMER: bytes.fromhex("050102e803"),
        characteristics.AIRING: bytes.fromhex("01261ee803"),
        characteristics.PAUSE: bytes.fromhex("010a"),
        characteristics.BOOST: bytes.fromhex("0160095802"),
    }

    def make_backend(_device, *, disconnected_callback, **kwargs):
        backend = backends[len(callbacks)]
        callbacks.append(disconnected_callback)

        async def close():
            disconnected_callback()

        backend.disconnect.side_effect = close
        return backend

    async def read(_client, characteristic, **kwargs):
        await asyncio.sleep(0)
        return packets[characteristic]

    factory = Mock(side_effect=make_backend)

    def initialize(client, ble_device, *, disconnected_callback, **kwargs):
        client._backend = factory(
            ble_device, disconnected_callback=partial(disconnected_callback, client)
        )
        client._pair_before_connect = False

    with (
        patch.object(BleakClient, "__init__", new=initialize),
        patch("bleak_retry_connector.IS_LINUX", False),
        patch("bleak_retry_connector.wait_for_disconnect", new_callable=AsyncMock),
        patch.object(
            BleakClient, "read_gatt_char", autospec=True, side_effect=read
        ) as reads,
    ):
        yield SimpleNamespace(
            device=device,
            backends=backends,
            callbacks=callbacks,
            factory=factory,
            reads=reads,
            read=read,
        )


@pytest.fixture
def update_deadlines():
    """Expose real deadlines so tests expire them only after I/O starts."""
    original_timeout = asyncio.timeout
    deadlines = []

    def timeout(delay):
        deadline = original_timeout(delay)
        if delay == 3600:
            deadlines.append(deadline)
        return deadline

    with (
        patch("pyfreshintellivent.device.UPDATE_TIMEOUT", 3600),
        patch("asyncio.timeout", side_effect=timeout),
    ):
        yield deadlines


@pytest.fixture(params=["reader", "connector"])
def connection_deadlines(request, update_deadlines):
    """Cover both the caller deadline and the connector's internal deadline."""
    if request.param == "reader":
        yield update_deadlines
    else:
        with patch(
            "bleak_retry_connector.asyncio_timeout",
            side_effect=lambda delay: asyncio.timeout(3600),
        ):
            yield update_deadlines


@pytest.mark.asyncio
async def test_partial_connect_retry_does_not_poison_successful_session(transport):
    """The connector's internal retry survives its earlier disconnect callback."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=1)
    backend = transport.backends[0]
    backend.connect.side_effect = [BleakError("partial connection failed"), None]

    async with asyncio.timeout(5):
        result = await reader.update_device(transport.device)

    assert result.sensors.rpm == 1234
    assert backend.connect.await_count == 2
    assert backend.disconnect.await_count == 2
    assert transport.factory.call_count == 1
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cleanup_error", [BleakError("cleanup failed"), asyncio.CancelledError()]
)
async def test_connect_deadline_cleanup_failure_prevents_retry(
    transport, connection_deadlines, cleanup_error
):
    """An uncertain partial connection must not be followed by another session."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=2)
    backend = transport.backends[0]
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def connect(*args, **kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    backend.connect.side_effect = connect

    make_backend = transport.factory.side_effect

    def failing_backend(*args, **kwargs):
        result = make_backend(*args, **kwargs)
        result.disconnect.side_effect = cleanup_error
        return result

    transport.factory.side_effect = failing_backend
    with patch.object(reader, "_sleep_before_retry", new_callable=AsyncMock):
        task = asyncio.create_task(reader.update_device(transport.device))
        try:
            async with asyncio.timeout(5):
                await entered.wait()
                connection_deadlines[-1].reschedule(asyncio.get_running_loop().time())
                with pytest.raises(ConnectionCleanupError):
                    await task
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    assert entered.is_set()
    assert cancelled.is_set()
    backend.connect.assert_awaited_once()
    backend.disconnect.assert_awaited_once()
    assert len(transport.callbacks) == 1
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
async def test_disconnect_callback_interrupts_read_before_retry(transport):
    """A real notification cancels the read; stale notifications stay isolated."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=2)
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def read(client, characteristic, **kwargs):
        if client._backend is transport.backends[0]:
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        transport.backends[0].disconnect.assert_awaited_once()
        transport.callbacks[0]()
        return await transport.read(client, characteristic, **kwargs)

    transport.reads.side_effect = read
    with patch.object(reader, "_sleep_before_retry", new_callable=AsyncMock):
        task = asyncio.create_task(reader.update_device(transport.device))
        try:
            async with asyncio.timeout(5):
                await entered.wait()
                transport.callbacks[0]()
                result = await task
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    assert cancelled.is_set()
    assert result.sensors.rpm == 1234
    assert len(transport.callbacks) == 2
    transport.backends[1].disconnect.assert_awaited_once()
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
async def test_operation_deadline_cancels_read_and_finishes_cleanup(
    transport, update_deadlines
):
    """The actual deadline cancels OS I/O and releases the reader for reuse."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=1)
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def read(*args, **kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    transport.reads.side_effect = read
    task = asyncio.create_task(reader.update_device(transport.device))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
            update_deadlines[-1].reschedule(asyncio.get_running_loop().time())
            with pytest.raises(FreshIntelliventTimeoutError):
                await task
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    assert cancelled.is_set()
    transport.backends[0].disconnect.assert_awaited_once()
    assert not reader._update_lock.locked()
    transport.reads.side_effect = transport.read
    async with asyncio.timeout(5):
        result = await reader.update_device(transport.device)
    assert result.sensors.rpm == 1234
    transport.backends[1].disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_during_successful_connect_is_not_lost(transport):
    """Only failed-attempt notifications may be discarded during connection."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=1)

    async def connect(*args, **kwargs):
        transport.callbacks[0]()
        await asyncio.sleep(0)

    transport.backends[0].connect.side_effect = connect
    async with asyncio.timeout(5):
        with pytest.raises(DisconnectedError):
            await reader.update_device(transport.device)
    transport.backends[0].connect.assert_awaited_once()
    transport.backends[0].disconnect.assert_awaited_once()
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
async def test_external_connect_cancellation_preserved_when_cleanup_fails(transport):
    """External cancellation keeps its identity even after cleanup fails."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=2)
    entered = asyncio.Event()

    async def connect(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    transport.backends[0].connect.side_effect = connect
    task = asyncio.create_task(reader.update_device(transport.device))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
            transport.backends[0].disconnect.side_effect = BleakError("cleanup failed")
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    transport.backends[0].connect.assert_awaited_once()
    transport.backends[0].disconnect.assert_awaited_once()
    assert len(transport.callbacks) == 1
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
async def test_connect_deadline_during_cleanup_preserves_cleanup_failure(
    transport, update_deadlines
):
    """A deadline during partial-connection cleanup must not permit retry."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=2)
    entered = asyncio.Event()
    release = asyncio.Event()
    transport.backends[0].connect.side_effect = BleakError("partial connection failed")

    async def cleanup():
        entered.set()
        await release.wait()
        raise BleakError("cleanup failed")

    make_backend = transport.factory.side_effect

    def failing_backend(*args, **kwargs):
        backend = make_backend(*args, **kwargs)
        backend.disconnect.side_effect = cleanup
        return backend

    transport.factory.side_effect = failing_backend
    with patch.object(reader, "_sleep_before_retry", new_callable=AsyncMock):
        task = asyncio.create_task(reader.update_device(transport.device))
        try:
            async with asyncio.timeout(5):
                await entered.wait()
                update_deadlines[-1].reschedule(asyncio.get_running_loop().time())
                await asyncio.sleep(0)
                release.set()
                with pytest.raises(ConnectionCleanupError):
                    await task
        finally:
            release.set()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    transport.backends[0].connect.assert_awaited_once()
    transport.backends[0].disconnect.assert_awaited_once()
    assert len(transport.callbacks) == 1
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
async def test_client_without_optional_disconnect_callback(transport):
    """Standalone clients can connect and close without an event subscriber."""
    from pyfreshintellivent.connection import ClientWithCleanup

    client = ClientWithCleanup(transport.device)
    async with asyncio.timeout(5):
        await client.connect()
        await client.disconnect()
    transport.backends[0].connect.assert_awaited_once()
    transport.backends[0].disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_exhausted_connector_retries_propagate_after_cleanup(transport):
    """A failed connection budget raises its transport error without reading."""
    from bleak_retry_connector import MAX_CONNECT_ATTEMPTS

    reader = FreshIntelliventBluetoothDeviceData(max_attempts=1)
    backend = transport.backends[0]
    backend.connect.side_effect = BleakError("connect failed")
    async with asyncio.timeout(5):
        with pytest.raises(BleakError):
            await reader.update_device(transport.device)
    assert backend.connect.await_count == MAX_CONNECT_ATTEMPTS
    assert backend.disconnect.await_count == MAX_CONNECT_ATTEMPTS
    assert transport.factory.call_count == 1
    transport.reads.assert_not_awaited()
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "connect_error", [None, BleakError("partial connection failed")]
)
async def test_backend_cleanup_cancellation_is_failure_not_caller_cancel(
    transport, connect_error
):
    """Self-cancelled cleanup must report failure instead of cancelling a poll."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=2)
    transport.backends[0].connect.side_effect = connect_error
    make_backend = transport.factory.side_effect

    def failing_backend(*args, **kwargs):
        backend = make_backend(*args, **kwargs)
        backend.disconnect.side_effect = asyncio.CancelledError()
        return backend

    transport.factory.side_effect = failing_backend
    async with asyncio.timeout(5):
        with pytest.raises(ConnectionCleanupError):
            await reader.update_device(transport.device)
    transport.backends[0].connect.assert_awaited_once()
    transport.backends[0].disconnect.assert_awaited_once()
    assert len(transport.callbacks) == 1
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
@pytest.mark.parametrize("retry", [False, True])
async def test_disconnect_with_unreadable_address_interrupts_and_cleans_up(
    transport, retry
):
    """Backend teardown cannot prevent disconnect delivery or later recovery."""
    reader = FreshIntelliventBluetoothDeviceData(max_attempts=2 if retry else 1)
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def read(client, characteristic, **kwargs):
        if client._backend is transport.backends[0]:
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        transport.backends[0].disconnect.assert_awaited_once()
        return await transport.read(client, characteristic, **kwargs)

    transport.reads.side_effect = read
    with patch.object(reader, "_sleep_before_retry", new_callable=AsyncMock):
        task = asyncio.create_task(reader.update_device(transport.device))
        try:
            async with asyncio.timeout(5):
                await entered.wait()
                with patch.object(
                    BleakClient,
                    "address",
                    new_callable=PropertyMock,
                    side_effect=AttributeError("backend already removed"),
                ) as address:
                    transport.callbacks[0]()
                    address.assert_not_called()
                if retry:
                    result = await task
                    assert result.sensors.rpm == 1234
                else:
                    with pytest.raises(DisconnectedError):
                        await task
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    assert cancelled.is_set()
    transport.backends[0].disconnect.assert_awaited_once()
    assert not reader._update_lock.locked()
    assert len(transport.callbacks) == (2 if retry else 1)
