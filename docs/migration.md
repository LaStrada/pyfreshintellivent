# Migrating from the legacy API

Replace `FreshIntelliVent` with
`FreshIntelliventBluetoothDeviceData.update_device(BLEDevice)`. Each call returns
new data; consumers must replace their previous result. Device writes are no
longer part of the reader API.

## Sensor fields

| Earlier field | Replacement |
| --- | --- |
| `humidity` | `humidity_raw`; no validated percentage conversion. |
| `temperature` from offset 4 | Byte 13; offset 4 is `voc_raw`. |
| `temperature_avg` | Removed; offset 10 is `reference_raw`. |
| `authenticated` | Removed; authentication uses a separate confirmation characteristic. |
| `status` | `flags_raw`. |
| `unknowns` | Named raw/reference/minutes/temperature/error fields. |
| Exact `mode_raw` lookup | Separate `active_trigger` and `motor_speed_code`. |

Keep historical statistics separate when a sensor's meaning changes.
Humidity configuration settings remain readable.

## Settings and authentication

- VOC and light sensitivity use 1=Low, 2=Medium, 3=High in both directions.
- Keys must contain four bytes or eight hex characters. Empty and all-zero keys
  are rejected; only `None` selects anonymous reads.
- Authentication requires confirmation from the fan, not just a write acknowledgement.
- Replacing a key takes effect on the next connection attempt. Invalid replacements
  preserve the previous key.
- Discovery matches device names; the generic Device Information service `0x180A`
  alone no longer identifies a Fresh fan.
