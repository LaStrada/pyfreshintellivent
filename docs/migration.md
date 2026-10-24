# Migrating to the unreleased 1.0 API

This is a major rewrite. Do not install it under a HACS integration that expects
the 0.3.x connection/write API. Develop and test the caller against this branch
in isolation first; retain a supported production version until rollout is ready.

Use `FreshIntelliventBluetoothDeviceData.update_device(BLEDevice)` to obtain a
new snapshot. The old `FreshIntelliVent` API is not available. Read current
coordinator data on each update; do not retain an initial snapshot inside entities.

| Earlier sensor field | Replacement / reason |
| --- | --- |
| `humidity` | Removed. `humidity_raw` has no validated percent conversion. |
| `temperature` decoded from offset 4 | Corrected to byte 13. Offset 4 is `voc_raw`. |
| `temperature_avg` | Removed. Offset 10 is `reference_raw`. |
| `authenticated` | Removed. It was the high byte of `light_raw`; PIN confirmation now validates authentication. |
| `status` | Removed; use `flags_raw` only with documented bit meanings. |
| `unknowns` | Replaced with named raw/reference/minutes/temperature/error fields. |
| Exact `mode_raw` lookup | `active_trigger` and `motor_speed_code`; unknown combinations stay unknown. |

Do not combine old temperature or humidity statistics with corrected sensors.
A HA integration should not expose humidity and should use new unique IDs for
any measurement whose meaning changed. Existing humidity configuration settings
are distinct from a humidity measurement and remain readable.

VOC decoding now agrees with the encoder: 1=Low, 2=Medium, 3=High. If a device
previously appeared to revert between Low and High, capture the raw setting and
compare with its current app before issuing further writes. Light sensitivity now
also preserves raw 1 as Low instead of normalizing it to Medium; a read/encode
round trip no longer changes that setting to 2.

Authentication keys must contain exactly four nonzero-as-a-whole bytes or eight
hex characters. A write acknowledgement is insufficient; the PIN confirmation
characteristic must return 1. Previously tolerated bad keys now fail explicitly.

Scan results no longer include arbitrary devices with service 0x180A. Use the
current advertisement name or a known address supplied by your platform.
