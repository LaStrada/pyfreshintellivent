# SKY Bluetooth protocol

This reference defines the UUIDs, packet layouts and decoding rules used by the
reader and encoders. Numeric words are unsigned and little-endian; offsets are
zero-based and lengths are in bytes. Configuration flags occupy one byte: the
reader treats nonzero as true, and encoders write 0 or 1.

## Services and characteristics

| Service UUID | Purpose |
| --- | --- |
| `0000180a-0000-1000-8000-00805f9b34fb` | Standard Device Information; not specific to Fresh |
| `1a46a853-e5ed-4696-bac0-70e346884a26` | SKY status service |

The reader resolves characteristics by UUID. This is not a complete GATT inventory.

| Characteristic UUID | Purpose | Payload / library use |
| --- | --- | --- |
| `b85fa07a-9382-4838-871c-81d045dcc2ff` | Device alias | UTF-8 string, trailing NULs removed; read into `name` |
| `528b80e8-c47a-4c0a-bdf1-916a7748f412` | Sensor/status | Exactly 15 bytes; see status layout below |
| `4cad343a-209a-40b7-b911-4d9b3df569b2` | Authentication key exchange | Four bytes; written to authenticate, read only for explicit pairing |
| `d1ae6b70-ee12-4f6d-b166-d2063dcaffe1` | Authentication confirmation | Nonempty response; first byte is interpreted |

Standard Device Information characteristics use the Bluetooth base UUID
`0000xxxx-0000-1000-8000-00805f9b34fb`:

| Short UUID | Field | Decoding |
| --- | --- | --- |
| `2a24` | `info.model_number` | UTF-8, trailing NULs removed |
| `2a26` | `info.fw_version` | UTF-8, trailing NULs removed |
| `2a27` | `info.hw_version` | UTF-8, trailing NULs removed |
| `2a28` | `info.sw_version` | UTF-8, trailing NULs removed |
| `2a29` | `info.manufacturer` | UTF-8, trailing NULs removed |

UUID constants are defined in [characteristics.py](pyfreshintellivent/characteristics.py).

## Authentication

Authentication uses an application-level four-byte key. This exchange is separate
from operating-system Bluetooth pairing or bonding.

Write the key to `4cad343a-209a-40b7-b911-4d9b3df569b2` with a GATT response.
The reader waits one second, then reads `d1ae6b70-ee12-4f6d-b166-d2063dcaffe1`.
First byte `01` confirms authentication; an empty response or another value
raises `AuthenticationError`. Trailing bytes are ignored.

With no key, the reader skips authentication. See
[anonymous read testing](docs/verification.md#authentication-and-anonymous-reads).

During physical pairing, the key can be read from its characteristic. Enable
pairing according to the fan's manual, then call
[`reader.pair_device()`](docs/api.md#physical-pairing). Keep returned keys private.

## Sensor packet

Characteristic `528b80e8-c47a-4c0a-bdf1-916a7748f412` must contain exactly 15 bytes.
Its SKY status service UUID is `1a46a853-e5ed-4696-bac0-70e346884a26`.

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
Off and 1 is Constant speed; other combinations remain unknown. Motor codes
include 0 off, 1 constant, 2 timer, 3 humidity, 4 automatic cycles,
5 odour. RPM is a separate actual measurement, not derivable from these codes.

`0x34` and `0x54` therefore both mean a VOC trigger. Exact-byte lookup tables lose
valid modes when the upper nibble changes.

Humidity, VOC and light are raw readings with no validated conversion to
percent, ppb or lux. Temperature is byte 13; its accuracy remains unverified.
Bytes 10–11 are not an average temperature, and byte 7 is not an authentication flag.

## Configuration packets

All UUIDs below use suffix `-2f33-11e7-93ae-92361f002671`.

| UUID prefix | Setting | Bytes | Fields in wire order |
| --- | --- | --- | --- |
| `7c4adc01` | Humidity | 4 | enabled u8, sensitivity u8, RPM u16 |
| `7c4adc02` | Presence/light and odour | 4 | light enabled u8, level u8, odour enabled u8, level u8 |
| `7c4adc03` | Constant/trickle | 3 | enabled u8, RPM u16 |
| `7c4adc04` | Timer | 5 | runtime minutes u8, delay enabled u8, delay minutes u8, RPM u16 |
| `7c4adc05` | Automatic airing | 5 | enabled u8, cycle period u8, active minutes u8, RPM u16 |
| `7c4adc06` | Pause | 2 | active u8, remaining minutes u8 |
| `7c4adc07` | Boost | 5 | active u8, RPM u16, remaining seconds u16 |
| `7c4adc08` | Motor test | 3 | enabled u8, RPM u16 |

`u8` and `u16` mean unsigned 8- and 16-bit values; flags follow the encoding
rule above. The seven configuration readers require the exact listed lengths.
Motor test has a packet encoder only and is not read by the library. Packet encoders
produce bytes; they do not send writes or verify that firmware applied a change.

Light and VOC sensitivity levels are 1 low, 2 medium, 3 high in both readers
and encoders. See [#52](https://github.com/LaStrada/pyfreshintellivent/issues/52)
for a conflicting VOC ordering report.

Known encoder limits: RPM clamps to 800–2400. Negative airing, boost and pause
durations clamp to zero. Timer duration and delay are encoded directly as unsigned
bytes (0–255); out-of-range values raise `struct.error`. Airing and pause durations
must fit 0–255 minutes, and boost must fit 0–65535 seconds after negative values
are clamped. Values above these limits raise `struct.error`; they are not clamped.
The airing encoder defaults to cycle period 26;
pass the freshly read `cycle_period` explicitly to preserve it. Setting changes
need a read-current/write/readback transaction around these encoders. ICE's reported minimum 700 RPM
requires model-specific validation before ICE writes can be supported.

The first byte of constant-speed settings is an enabled flag, not an opcode.
Changing only RPM requires preserving the current enabled byte. A stale cached
false value will disable constant mode even when the write itself succeeds.

## Readback and operating state

A GATT write acknowledgement, stored settings, active trigger and measured RPM
are separate observations. Read back configuration to confirm stored values;
mode changes and motor spin-up can take effect later. Another trigger may also
override a configured mode. Sequential characteristic reads are not an atomic
firmware snapshot. Preserve fresh sibling fields when encoding an update.

Firmware may normalize requested values. Report confirmed readback.

## Related reports

- [VOC ordering dispute, library #52](https://github.com/LaStrada/pyfreshintellivent/issues/52)
- [VOC raw mode 84, HACS #60](https://github.com/angoyd/freshintelliventHacs/issues/60)
- [Constant-speed update clears enabled, HACS #56](https://github.com/angoyd/freshintelliventHacs/issues/56)
- [ICE minimum speed report, HACS #52](https://github.com/angoyd/freshintelliventHacs/issues/52)
