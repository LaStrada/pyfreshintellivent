"""Replay sanitized SKY hardware responses through the complete reader.

Recorded frames are inputs, and the fixture's expected values are fixed literals.
Only BLE I/O and authentication delay are replaced; decoding, authentication,
new-snapshot allocation and connection cleanup execute normally. These tests do
not emulate firmware writes or assert a control queue that does not exist yet.
"""

import json
from copy import deepcopy
from dataclasses import asdict, fields
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from bleak.backends.device import BLEDevice

from pyfreshintellivent import characteristics
from pyfreshintellivent.device import FreshIntelliventBluetoothDeviceData
from pyfreshintellivent.models import FreshIntelliventDevice
from pyfreshintellivent.parser import SkyModeParser

_FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "sky_hardware_snapshots.json").read_text(
        encoding="utf-8"
    )
)
_RECORDS = _FIXTURE["snapshots"]
_BY_LABEL = {record["label"]: record for record in _RECORDS}


async def _read_snapshot(reader, record):
    """Use recorded payloads without allowing real BLE or any mode writes."""
    ble_device = BLEDevice("00:00:00:00:00:00", "SKY fixture", {})
    packets = {
        UUID(characteristic): bytearray.fromhex(payload)
        for characteristic, payload in record["packets"].items()
    }
    packets.update(
        {
            characteristics.AUTH_CONFIRMATION: b"\x01",
            characteristics.DEVICE_NAME: b"SKY fixture",
            characteristics.MODEL_NUMBER: _FIXTURE["model_number"].encode(),
            characteristics.FIRMWARE_VERSION: _FIXTURE["firmware"].encode(),
            characteristics.HARDWARE_VERSION: _FIXTURE["hardware"].encode(),
            characteristics.SOFTWARE_VERSION: b"fixture",
            characteristics.MANUFACTURER_NAME: b"Fresh",
        }
    )
    client = AsyncMock(address=ble_device.address)
    client.read_gatt_char.side_effect = packets.__getitem__
    with (
        patch("pyfreshintellivent.device.establish_connection", return_value=client),
        patch("pyfreshintellivent.device.asyncio.sleep", new_callable=AsyncMock),
    ):
        snapshot = await reader.update_device(ble_device)
    client.disconnect.assert_awaited_once()
    client.write_gatt_char.assert_awaited_once_with(
        characteristics.AUTH, bytearray(b"test"), response=True
    )
    assert {call.args[0] for call in client.read_gatt_char.await_args_list} == set(
        packets
    )
    assert not reader._update_lock.locked()
    return snapshot


def _assert_record(snapshot, record):
    """Compare every sensor and mode field against the frozen expected snapshot."""
    assert asdict(snapshot.sensors) == record["expected_sensors"]
    expected_modes = deepcopy(_FIXTURE["baseline_expected_modes"])
    expected_modes.update(record["expected_mode_changes"])
    assert asdict(snapshot.modes) == expected_modes


@pytest.mark.asyncio
@pytest.mark.parametrize("record", _RECORDS, ids=lambda record: record["label"])
async def test_recorded_hardware_snapshot(record):
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    snapshot = await _read_snapshot(reader, record)
    _assert_record(snapshot, record)


@pytest.mark.asyncio
async def test_later_reads_leave_all_retained_snapshots_unchanged():
    """A coordinator can retain old state while the same reader polls new data."""
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    assert len(_RECORDS) >= 2
    retained = []
    for record in _RECORDS:
        latest = await _read_snapshot(reader, record)
        _assert_record(latest, record)
        for previous, previous_record in retained:
            assert latest is not previous
            assert latest.sensors is not previous.sensors
            assert latest.modes is not previous.modes
            assert latest.info is not previous.info
            for field in fields(latest.modes):
                assert getattr(latest.modes, field.name) is not getattr(
                    previous.modes, field.name
                )
            assert (
                latest.modes.light_and_voc.light
                is not previous.modes.light_and_voc.light
            )
            assert (
                latest.modes.light_and_voc.voc is not previous.modes.light_and_voc.voc
            )
            assert latest.modes.timer.delay is not previous.modes.timer.delay
            _assert_record(previous, previous_record)
        retained.append((latest, record))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "before,after,changed,preserved",
    [
        ("baseline", "light_voc_1", "light", "voc"),
        ("light_voc_1", "light_voc_2", "voc", "light"),
        ("light_voc_2", "light_voc_3", "light", "voc"),
        ("light_voc_3", "light_voc_4", "voc", "light"),
        ("light_voc_4", "light_voc_5", "light", "voc"),
        ("light_voc_5", "light_voc_6", "voc", "light"),
        ("light_voc_6", "light_voc_7", "light", "voc"),
        ("light_voc_7", "light_voc_8", "voc", "light"),
    ],
)
async def test_light_and_voc_changes_keep_the_other_settings(
    before, after, changed, preserved
):
    """Shared-characteristic reads must retain the untouched sibling settings."""
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    previous = await _read_snapshot(reader, _BY_LABEL[before])
    latest = await _read_snapshot(reader, _BY_LABEL[after])
    old_settings = previous.modes.light_and_voc
    new_settings = latest.modes.light_and_voc
    assert getattr(new_settings, preserved) == getattr(old_settings, preserved)
    assert getattr(new_settings, changed) != getattr(old_settings, changed)
    _assert_record(previous, _BY_LABEL[before])
    _assert_record(latest, _BY_LABEL[after])


@pytest.mark.asyncio
async def test_constant_rpm_changes_and_enable_toggles_keep_independent_fields():
    """The active flag is not inferred from RPM, and toggling it retains RPM."""
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    for label, enabled, rpm in [
        ("baseline", True, 1200),
        ("constant_1", True, 1300),
        ("constant_2", True, 1400),
        ("constant_3", False, 1400),
        ("constant_4", True, 1400),
    ]:
        snapshot = await _read_snapshot(reader, _BY_LABEL[label])
        assert snapshot.modes.constant_speed.enabled is enabled
        assert snapshot.modes.constant_speed.rpm == rpm
        _assert_record(snapshot, _BY_LABEL[label])


@pytest.mark.asyncio
async def test_airing_rpm_change_retains_cycle_period_and_duration():
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    previous = await _read_snapshot(reader, _BY_LABEL["baseline"])
    latest = await _read_snapshot(reader, _BY_LABEL["airing_1"])
    assert previous.modes.airing.rpm == 800
    assert latest.modes.airing.rpm == 900
    assert previous.modes.airing.cycle_period == latest.modes.airing.cycle_period == 26
    assert previous.modes.airing.minutes == latest.modes.airing.minutes == 119
    assert previous.modes.airing.enabled is latest.modes.airing.enabled is False


def test_recorded_airing_readback_can_differ_from_encoded_request():
    """This firmware returned 15 minutes for a 5-minute request; readback wins.

    Keep the raw encoder contract, without assuming every firmware clamps alike.
    Future controls must publish confirmed readback rather than the request.
    """
    observation = _FIXTURE["airing_duration_observation"]
    parser = SkyModeParser()
    request = parser.airing_write(
        False, observation["requested_minutes"], 900, cycle_period=26
    )
    assert request == bytes.fromhex(observation["written"])
    actual = parser.airing_read(bytes.fromhex(observation["read_back"]))
    assert actual == observation["expected_read_back"]
    assert actual["minutes"] != observation["requested_minutes"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "record", _FIXTURE["sensor_snapshots"], ids=lambda record: record["label"]
)
async def test_recorded_transient_sensor_snapshot(record):
    """Fast status captures do not pretend a simultaneous full settings read."""
    reader = FreshIntelliventBluetoothDeviceData()
    device = FreshIntelliventDevice()
    client = AsyncMock()
    client.read_gatt_char.return_value = bytearray.fromhex(record["packet"])
    await reader.get_sensor_data(client, device, raise_on_not_found=True)
    client.read_gatt_char.assert_awaited_once_with(characteristics.DEVICE_STATUS)
    client.write_gatt_char.assert_not_awaited()
    assert asdict(device.sensors) == record["expected_sensors"]


@pytest.mark.asyncio
async def test_mixed_sequence_retains_earlier_changes_after_reconnect():
    """Replay observed cumulative settings without inventing a write queue."""
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    retained = []
    for index in range(1, 9):
        record = _BY_LABEL[f"burst_mixed_{index}"]
        snapshot = await _read_snapshot(reader, record)
        _assert_record(snapshot, record)
        retained.append(snapshot)
    assert retained[6].modes == retained[7].modes  # Idempotent enabled=True write.
    latest = await _read_snapshot(reader, _BY_LABEL["burst_after_reconnect"])
    assert latest.modes == retained[-1].modes
    for index, previous in enumerate(retained, 1):
        _assert_record(previous, _BY_LABEL[f"burst_mixed_{index}"])


@pytest.mark.asyncio
async def test_rapid_constant_settings_retain_enabled_and_other_modes():
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    for index, rpm in enumerate(
        [1200, 1300, 1400, 1500, 1200, 1300, 1400, 1500, 1200, 1300], 1
    ):
        record = _BY_LABEL[f"burst_constant_{index}"]
        snapshot = await _read_snapshot(reader, record)
        assert snapshot.modes.constant_speed.enabled is True
        assert snapshot.modes.constant_speed.rpm == rpm
        _assert_record(snapshot, record)


@pytest.mark.asyncio
async def test_pause_and_boost_can_both_be_enabled_while_pause_is_active():
    """Enabled settings and the active sensor trigger are separate state."""
    reader = FreshIntelliventBluetoothDeviceData(authentication_code=b"test")
    record = _BY_LABEL["overlay_sequential_observation"]
    snapshot = await _read_snapshot(reader, record)
    assert snapshot.modes.boost.enabled is True
    assert snapshot.modes.pause.enabled is True
    assert snapshot.sensors.mode == "Pause"
    assert snapshot.sensors.active_trigger == 6
    assert snapshot.sensors.rpm == 0
    _assert_record(snapshot, record)
