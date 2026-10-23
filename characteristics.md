# SKY Bluetooth protocol

All multibyte numeric fields are unsigned, little-endian. UUID 0x180A is the
standard Device Information service and **cannot identify a Fresh device**.
Name matching is only a discovery hint; successful protocol reads still matter.

## Evidence and confidence

The old Fresh Ventilation 2.3.2 Android app and Fresh Connect 2.2.1 Android app
were independently inspected from owner-supplied packages. The first contains Java
SKY request classes; the second contains Hermes v98 bytecode. Decompiled code is
imperfect and remains private. This document records interoperable packet facts,
not proprietary source. Both apps agree on offsets 0–9; Fresh Connect supplies
fields 10–14 and the trigger/motor bit fields. No claim is made that every firmware
revision behaves identically.

Public cross-checks:

- [VOC ordering dispute, library #52](https://github.com/LaStrada/pyfreshintellivent/issues/52)
- [VOC raw mode 84, HACS #60](https://github.com/angoyd/freshintelliventHacs/issues/60)
- [Constant-speed update clears enabled, HACS #56](https://github.com/angoyd/freshintelliventHacs/issues/56)
- [ICE minimum speed report, HACS #52](https://github.com/angoyd/freshintelliventHacs/issues/52)

## Authentication

Write the four-byte key to `4cad343a-209a-40b7-b911-4d9b3df569b2` with a GATT
response, then read `d1ae6b70-ee12-4f6d-b166-d2063dcaffe1`. The reader waits one
second for processing and accepts first byte `01`; empty or negative replies
raise `AuthenticationError`. A successful write alone is not authentication.
The old Android app compares confirmation with resource value 1; Fresh Connect
reads its first byte as a boolean. Requiring 1 avoids accepting unknown replies.

In the documented SKY pairing procedure, reveal the touch controls and hold the
wireless button for roughly eight seconds, then read the key characteristic.
The key is not available as a nonzero value outside pairing mode. Follow the
manual for the actual model. Use `await reader.pair_device(ble_device)` while pairing is enabled. It verifies
the key, reads a complete snapshot and finishes disconnect cleanup before returning
the key bytes and retaining them on the reader. Failure preserves any previous key. Never print key bytes in diagnostics or examples.

## Sensor packet

Characteristic `528b80e8-c47a-4c0a-bdf1-916a7748f412` must contain exactly 15 bytes.
The application calls its service `1a46a853-e5ed-4696-bac0-70e346884a26` the SKY
status service.

| Offset | Width | Meaning | Library field |
| --- | --- | --- | --- |
| 0 | 1 | Trigger flags | `flags_raw` |
| 1 | 1 | Low nibble active trigger; high nibble motor-speed code | `mode_raw`, `active_trigger`, `motor_speed_code` |
| 2 | 2 | Uncalibrated humidity level | `humidity_raw` |
| 4 | 2 | Odour sensor level | `voc_raw` |
| 6 | 2 | Light level | `light_raw` |
| 8 | 2 | Actual RPM | `rpm` |
| 10 | 2 | Reference level | `reference_raw` |
| 12 | 1 | Minutes active | `minutes_active` |
| 13 | 1 | Temperature byte | `temperature` |
| 14 | 1 | Device error code | `error_code` |

Byte 0 bits 0–4 are LS input, presence, humidity high, humidity sinking and odour
active. Bits 5–7 encode touch-button/humidity trigger context. The library keeps
this byte raw rather than calling any nonzero value a generic status flag.

Active triggers: 0 none, 1 humidity, 2 presence/light, 3 timer, 4 odour/VOC,
5 automatic airing, 6 pause, 7 boost, 8 motor test, 9 humidity sinking,
11 delayed start. Other values remain unknown. When trigger=0, motor code 0 is
Off and 1 is Constant speed; other combinations remain unknown. Motor codes in
Fresh Connect include 0 off, 1 constant, 2 timer, 3 humidity, 4 automatic cycles,
5 odour. RPM is a separate actual measurement, not derivable from these codes.

`0x34` and `0x54` therefore both mean a VOC trigger. Exact-byte lookup tables lose
valid modes when the upper nibble changes.

**Do not expose relative humidity, lux, ppb or a VOC index from the raw fields.**
There is no established calibration. Temperature has app protocol evidence but
still needs comparison with hardware; its sensor location and accuracy are not
established. Bytes 10–11 are not an average temperature. Byte 7 is not an
authentication flag.

## Configuration packets

All UUIDs below use suffix `-2f33-11e7-93ae-92361f002671`.

| Prefix | Setting | Fields in order |
| --- | --- | --- |
| `7c4adc01` | Humidity | enabled u8, sensitivity u8, RPM u16 |
| `7c4adc02` | Presence/light and odour | light enabled u8, level u8, odour enabled u8, level u8 |
| `7c4adc03` | Constant/trickle | enabled u8, RPM u16 |
| `7c4adc04` | Timer | runtime minutes u8, delay enabled u8, delay minutes u8, RPM u16 |
| `7c4adc05` | Automatic airing | enabled u8, cycle period u8, active minutes u8, RPM u16 |
| `7c4adc06` | Pause | active u8, remaining minutes u8 |
| `7c4adc07` | Boost | active u8, RPM u16, remaining seconds u16 |
| `7c4adc08` | Motor test | enabled u8, RPM u16 |

Sensitivity levels are 1 low, 2 medium, 3 high. VOC used to decode in reverse
while encoding in normal order. Both inspected Android versions use normal order.
Issue #52 contains an older iOS observation to the contrary; cross-platform/live
comparison remains necessary before declaring every firmware verified. Light's
legacy low-to-medium UI normalization remains in the parser.

Known encoder limitations retained for compatibility: RPM clamps to 800–2400,
negative durations clamp to zero. The airing encoder defaults to cycle period
26 for old callers; pass the freshly read `cycle_period` explicitly to preserve it. These encoders must not serve as
an unchecked read-modify-write transaction layer. ICE's reported minimum 700 RPM
requires model-specific validation before ICE writes can be supported.

The first byte of constant-speed settings is an enabled flag, not an opcode.
Changing only RPM requires preserving the current enabled byte. A stale cached
false value will disable constant mode even when the write itself succeeds.

## Identification

Device alias: `b85fa07a-9382-4838-871c-81d045dcc2ff` (UTF-8).
Standard model/manufacturer/version characteristics are in `characteristics.py`.
Fresh Connect identifies the SKY protocol family by model number string `40`.
The app groups SKY/ICE with some other branded products, but shared protocol
families or UUIDs alone are not sufficient evidence to advertise full support.
