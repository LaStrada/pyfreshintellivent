"""Authentication boundaries with synthetic keys and isolated BLE I/O."""

import asyncio
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import AsyncMock, call, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from pyfreshintellivent import characteristics
from pyfreshintellivent.device import (
    AuthenticationError,
    FreshIntelliventBluetoothDeviceData,
)

_INVALID_CODES = [
    pytest.param("", ValueError, id="empty-string"),
    pytest.param("1234567", ValueError, id="short-hex"),
    pytest.param("123456789", ValueError, id="long-hex"),
    pytest.param("not-hex!", ValueError, id="non-hex"),
    pytest.param("0x123456", ValueError, id="hex-prefix"),
    pytest.param("１２３４ＡＢＣＤ", ValueError, id="fullwidth-hex"),
    pytest.param("12345678\n", ValueError, id="trailing-newline"),
    pytest.param("12 34 56", ValueError, id="embedded-spaces"),
    pytest.param(" 1234567", ValueError, id="leading-space"),
    pytest.param("00000000", ValueError, id="zero-hex"),
    pytest.param(b"", ValueError, id="empty-bytes"),
    pytest.param(b"abc", ValueError, id="short-bytes"),
    pytest.param(b"abcde", ValueError, id="long-bytes"),
    pytest.param(bytes(4), ValueError, id="zero-bytes"),
    pytest.param(bytearray(), ValueError, id="empty-bytearray"),
    pytest.param(bytearray(4), ValueError, id="zero-bytearray"),
    pytest.param(0, TypeError, id="zero-int"),
    pytest.param(12345678, TypeError, id="integer"),
    pytest.param(False, TypeError, id="false"),
    pytest.param(True, TypeError, id="true"),
    pytest.param(1.5, TypeError, id="float"),
    pytest.param([], TypeError, id="empty-list"),
    pytest.param({}, TypeError, id="empty-dict"),
    pytest.param(memoryview(b"test"), TypeError, id="memoryview"),
]


@pytest.fixture
def transport():
    """Keep authentication, all snapshot parsers and cleanup real."""
    device = BLEDevice("00:00:00:00:00:00", "SKY fixture", {})
    packets = {
        characteristics.AUTH_CONFIRMATION: b"\x01",
        characteristics.DEVICE_NAME: b"SKY fixture",
        characteristics.MODEL_NUMBER: b"40",
        characteristics.FIRMWARE_VERSION: b"fixture",
        characteristics.HARDWARE_VERSION: b"fixture",
        characteristics.SOFTWARE_VERSION: b"fixture",
        characteristics.MANUFACTURER_NAME: b"Fresh",
        characteristics.DEVICE_STATUS: bytes.fromhex("0010010002000300b0040400001d00"),
        characteristics.HUMIDITY: bytes.fromhex("0103d007"),
        characteristics.LIGHT_VOC: bytes.fromhex("01030103"),
        characteristics.CONSTANT_SPEED: bytes.fromhex("01b004"),
        characteristics.TIMER: bytes.fromhex("3c01050807"),
        characteristics.AIRING: bytes.fromhex("001a772003"),
        characteristics.PAUSE: bytes.fromhex("003c"),
        characteristics.BOOST: bytes.fromhex("0060095802"),
    }
    client = AsyncMock(address=device.address)
    client.read_gatt_char.side_effect = packets.__getitem__
    with (
        patch(
            "pyfreshintellivent.device.establish_connection", return_value=client
        ) as connect,
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
    ):
        yield SimpleNamespace(
            device=device, client=client, connect=connect, packets=packets
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("entrypoint", ["constructor", "setter", "authenticate"])
@pytest.mark.parametrize("value,error", _INVALID_CODES)
async def test_invalid_authentication_input_fails_before_ble(
    transport, entrypoint, value, error
):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"old!")
    with pytest.raises(error) as raised:
        if entrypoint == "constructor":
            FreshIntelliventBluetoothDeviceData(authentication_code=value)
        elif entrypoint == "setter":
            reader.authentication_code = value
        else:
            await reader.authenticate(transport.client, authentication_code=value)
    if isinstance(value, str) and value:
        assert value not in str(raised.value)
    assert reader.authentication_code == b"old!"
    transport.connect.assert_not_awaited()
    transport.client.write_gatt_char.assert_not_awaited()
    transport.client.read_gatt_char.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("entrypoint", ["constructor", "setter"])
async def test_mutating_original_bytearray_does_not_change_configured_key(
    transport, entrypoint
):
    key = bytearray(b"test")
    if entrypoint == "constructor":
        reader = FreshIntelliventBluetoothDeviceData(authentication_code=key)
    else:
        reader = FreshIntelliventBluetoothDeviceData()
        reader.authentication_code = key
    key[:] = bytes(4)
    assert reader.authentication_code == b"test"
    assert isinstance(reader.authentication_code, bytes)
    snapshot = await reader.update_device(transport.device)
    assert snapshot.sensors.rpm == 1200
    transport.client.write_gatt_char.assert_awaited_once_with(
        characteristics.AUTH, bytearray(b"test"), response=True
    )
    transport.client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_hex_string_representation_is_preserved(transport):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code="ABcD1234")
    assert reader.authentication_code == "ABcD1234"
    await reader.update_device(transport.device)
    transport.client.write_gatt_char.assert_awaited_once_with(
        characteristics.AUTH, bytearray.fromhex("abcd1234"), response=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("clear_previous_key", [False, True])
async def test_only_none_selects_anonymous_reads_without_key_acquisition(
    transport, clear_previous_key
):
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code=b"test" if clear_previous_key else None
    )
    reader.authentication_code = None
    snapshot = await reader.update_device(transport.device)
    assert snapshot.sensors.rpm == 1200
    transport.client.write_gatt_char.assert_not_awaited()
    requested = [
        item.args[0] for item in transport.client.read_gatt_char.await_args_list
    ]
    assert characteristics.AUTH not in requested
    assert characteristics.AUTH_CONFIRMATION not in requested
    transport.client.disconnect.assert_awaited_once()
    assert reader.authentication_code is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "before,after", [(b"old!", b"new!"), (b"old!", None), (None, b"new!")]
)
async def test_connection_attempt_uses_key_captured_before_connect(
    transport, before, after
):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=before)

    async def connect(*args, **kwargs):
        reader.authentication_code = after
        return transport.client

    transport.connect.side_effect = connect
    await reader.update_device(transport.device)
    if before is None:
        transport.client.write_gatt_char.assert_not_awaited()
    else:
        transport.client.write_gatt_char.assert_awaited_once_with(
            characteristics.AUTH, bytearray(before), response=True
        )
    assert reader.authentication_code == after
    transport.client.write_gatt_char.reset_mock()
    await reader.update_device(transport.device)
    if after is None:
        transport.client.write_gatt_char.assert_not_awaited()
    else:
        transport.client.write_gatt_char.assert_awaited_once_with(
            characteristics.AUTH, bytearray(after), response=True
        )
    assert transport.client.disconnect.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("reply", [b"", b"\x00", b"\x02", b"\xff", b"\x00\x01"])
async def test_rejected_confirmation_stops_snapshot_without_retry(transport, reply):
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code=b"test", max_attempts=3
    )
    transport.packets[characteristics.AUTH_CONFIRMATION] = reply
    with pytest.raises(AuthenticationError):
        await reader.update_device(transport.device)
    transport.connect.assert_awaited_once()
    transport.client.read_gatt_char.assert_awaited_once_with(
        characteristics.AUTH_CONFIRMATION
    )
    transport.client.disconnect.assert_awaited_once()
    assert reader.authentication_code == b"test"
    assert not reader._update_lock.locked()


@pytest.mark.asyncio
@pytest.mark.parametrize("reply", [b"\x01", b"\x01\x00", b"\x01\xff"])
async def test_positive_confirmation_preserves_first_byte_contract(transport, reply):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    transport.packets[characteristics.AUTH_CONFIRMATION] = reply
    snapshot = await reader.update_device(transport.device)
    assert snapshot.sensors.rpm == 1200
    transport.client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_corrected_key_recovers_after_rejection(transport):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"bad!")
    transport.packets[characteristics.AUTH_CONFIRMATION] = b"\x00"
    with pytest.raises(AuthenticationError):
        await reader.update_device(transport.device)
    assert reader.authentication_code == b"bad!"
    reader.authentication_code = b"good"
    transport.packets[characteristics.AUTH_CONFIRMATION] = b"\x01"
    snapshot = await reader.update_device(transport.device)
    assert snapshot.sensors.rpm == 1200
    assert transport.client.write_gatt_char.await_args_list == [
        call(characteristics.AUTH, bytearray(b"bad!"), response=True),
        call(characteristics.AUTH, bytearray(b"good"), response=True),
    ]
    assert transport.client.disconnect.await_count == 2
    assert transport.connect.await_count == 2
    assert reader.authentication_code == b"good"


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["write_gatt_char", "read_gatt_char"])
async def test_authentication_transport_failure_cleans_up_and_preserves_key(
    transport, operation, caplog
):
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code=b"test", max_attempts=1
    )
    getattr(transport.client, operation).side_effect = BleakError(
        "backend-key-material"
    )
    with caplog.at_level("DEBUG", logger="pyfreshintellivent.device"):
        with pytest.raises(BleakError):
            await reader.update_device(transport.device)
    transport.client.disconnect.assert_awaited_once()
    assert reader.authentication_code == b"test"
    assert not reader._update_lock.locked()
    assert "backend-key-material" not in caplog.text
    if operation == "write_gatt_char":
        transport.client.read_gatt_char.assert_not_awaited()
    else:
        transport.client.read_gatt_char.assert_awaited_once_with(
            characteristics.AUTH_CONFIRMATION
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["write_gatt_char", "read_gatt_char"])
async def test_cancellation_during_authentication_cleans_up_and_preserves_key(
    transport, operation
):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    entered = asyncio.Event()

    async def blocked(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    getattr(transport.client, operation).side_effect = blocked
    task = asyncio.create_task(reader.update_device(transport.device))
    try:
        async with asyncio.timeout(5):
            await entered.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    transport.client.disconnect.assert_awaited_once()
    transport.connect.assert_awaited_once()
    assert reader.authentication_code == b"test"
    assert not reader._update_lock.locked()
    if operation == "write_gatt_char":
        transport.client.read_gatt_char.assert_not_awaited()
    else:
        transport.client.read_gatt_char.assert_awaited_once_with(
            characteristics.AUTH_CONFIRMATION
        )


@pytest.mark.asyncio
async def test_direct_authentication_copies_bytearray_before_first_await(transport):
    reader = FreshIntelliventBluetoothDeviceData()
    code = bytearray(b"test")
    observed = []

    async def write(characteristic, value, *, response):
        code[:] = bytes(4)
        observed.append(bytes(value))

    transport.client.write_gatt_char.side_effect = write
    await reader.authenticate(transport.client, authentication_code=code)
    assert observed == [b"test"]
    assert reader.authentication_code is None


@pytest.mark.asyncio
async def test_key_replacement_applies_after_failed_attempt_cleanup(transport):
    """A retry captures the replacement key after the prior connection closes."""
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code=b"old!", max_attempts=2
    )
    previous = await reader.update_device(transport.device)
    previous_values = asdict(previous)
    transport.connect.reset_mock()
    transport.client.reset_mock()
    first = AsyncMock(address=transport.device.address)
    first.read_gatt_char.side_effect = BleakError("confirmation transport failed")
    attempt = 0

    async def connect(*args, **kwargs):
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            reader.authentication_code = b"new!"
            return first
        first.disconnect.assert_awaited_once()
        first.write_gatt_char.assert_awaited_once_with(
            characteristics.AUTH, bytearray(b"old!"), response=True
        )
        return transport.client

    transport.connect.side_effect = connect
    latest = await reader.update_device(transport.device)
    assert transport.connect.await_count == 2
    first.read_gatt_char.assert_awaited_once_with(characteristics.AUTH_CONFIRMATION)
    first.disconnect.assert_awaited_once()
    transport.client.write_gatt_char.assert_awaited_once_with(
        characteristics.AUTH, bytearray(b"new!"), response=True
    )
    transport.client.disconnect.assert_awaited_once()
    assert reader.authentication_code == b"new!"
    assert latest is not previous
    assert latest.sensors is not previous.sensors
    assert latest.modes is not previous.modes
    assert asdict(latest) == previous_values
    assert asdict(previous) == previous_values
    assert not reader._update_lock.locked()
