# Verification and device support

| Target | Evidence | Current claim |
| --- | --- | --- |
| Fresh Intellivent SKY | Packet contract, captured hardware regressions and attended SKY checks | Existing-key/anonymous reads, rejection/recovery, dev-HA polling/reload, configuration retention and bounded transient modes verified on one fan; broader acceptance pending |
| Fresh Intellivent ICE / ICE | HACS discovery and 700 RPM reports | Name discovery; reads provisional; no validated ICE write limits |
| Other Fresh products | Same vendor or app alone | Unsupported until protocol and hardware evidence exists |

## Automated verification

The test suite enforces 100% runtime statement and branch coverage. It covers:

- Connection/read/disconnect cancellation, deadlines and cleanup failures.
- Serialized reads, cancelled lock waiters, retries and connector callbacks.
- Authentication rejection, transport failures and failed pairing.
- Malformed packets, trigger/motor combinations, setting round trips and discovery.
- Captured hardware snapshots, independent nested state across reads, sibling
  settings and observed firmware normalization. See the [hardware fixtures](../tests/fixtures/sky_hardware_snapshots.json).

The [CI workflow](../.github/workflows/ci.yml) defines the active Python/platform
matrix. Simulated tests verify software behavior. Use the hardware checklist
below to validate physical interoperability.

## Hardware acceptance before release

Record model, firmware, app version, transport and date without the auth key.
For each applicable target verify:

1. Fresh startup and authenticated read; wrong key rejected; key never logged.
2. Ten sequential polls and overlapping callers; one connection at a time.
3. Cancellation during connecting and reading; a subsequent read succeeds.
4. HA unload/reload and controlled restart with no retained connection.
5. Proxy loss/recovery and nearest-proxy change without stale device objects.
6. Phone app connected/disconnected; sensible retry/backoff without a busy loop.
7. Sensor values compared with the app; no humidity percentage or invented units.
8. For future controls, capture settings, change one field, read back, restore
   in `finally`, and independently verify restoration. Preserve sibling fields.

## Recorded SKY check

On 2026-10-24, an Intellivent SKY reporting firmware `01.01` and hardware
`01.00` was checked with the [reader source at this commit](https://github.com/LaStrada/pyfreshintellivent/tree/3e81979927b39ec21323a6ba64c996dd49ad2ffb)
and a local development Home Assistant integration. The initial run had local
Bluetooth and an ESPHome proxy registered. The final run used only the ESPHome
proxy, with the local adapter disabled, and verified saved-key reads, a scheduled
poll, reload and disable/enable.

Verified on this fan:

- Manually initiated config flow authenticated with the existing key and read
  a complete snapshot; no new pairing was performed.
- Two scheduled polls across the runs returned fresh RPM readings. Boost and constant-speed modes
  were observed. The integration exposed RPM/mode, kept temperature disabled
  as a diagnostic entity, and created no humidity entity.
- Reloading the entry and disabling/re-enabling it each produced fresh readings.
- Dev HA shut down cleanly and the original HA installation resumed polling
  after Bluetooth ownership was returned.

The initial run was interrupted by an unconfirmed dev HTTP configuration's
restart deadline. The final run confirmed that configuration and completed
cleanly. This is a limited hardware check, not completion of the release checklist.
Physical pairing, ten scheduled HA polls, overlapping
library callers, cancellation during BLE operations, proxy loss/failover, phone contention and
sensor comparison with the app remain unverified on hardware. App version was
not recorded because no app comparison was performed. No control entity or
supported device-write API was exercised by the dev integration. Other firmware
and ICE support still require separate validation.


## State retention and bounded mode checks

Additional attended tests on the same SKY used the reader and packet encoders
through an ESPHome proxy. A separate test harness performed direct acknowledged
GATT writes after recording all original settings; it was not a supported
library device-write API or HA control entity.

- Ten authenticated disconnect/reconnect/read cycles retained all configuration
  packets and earlier snapshots.
- Single-field tests covered constant-speed RPM/enabled, humidity RPM/detection/
  enabled, independent light/VOC detection/enabled, timer duration/delay/RPM and
  airing RPM/duration/enabled. Other fields and mode packets were checked.
- Ten ordered RPM edits and eight interleaved field edits preserved cumulative
  state through a reconnect. Each transaction read, patched, wrote and read back.
- Twelve acknowledged speed writes without intervening reads took approximately
  0.71 seconds from first to last acknowledgement. Immediate and delayed reads
  retained the final 1500 rpm setting and unrelated fields. This verifies the
  final result, not that every intermediate speed was physically reached.
- A 60-second boost read back 58 seconds after about two seconds and reported
  trigger 7. With pause added, both flags remained enabled, boost had 55 seconds
  left, and the active trigger was pause (6). Behavior after pause expiry was not
  tested. Pause alone reported zero RPM. A short 1300 rpm motor test reported
  trigger 8 and 1327 measured RPM; off was acknowledged within about eight seconds.
- Original raw packets were restored and verified again across a fresh connection.
  Production HA resumed fresh polling after ownership was returned.

One concrete normalization was observed: an airing request for 5 minutes was
acknowledged but read back as 15 minutes, with the other fields unchanged. The
raw encoder remains unchanged: this observation does not establish a universal
minimum across firmware or devices. Controls must publish confirmed readback,
not assume that acknowledgement means the requested value was stored exactly.

The [snapshot tests](../tests/test_hardware_snapshots.py) replay 46 complete
captures and four separate transient sensor packets. Expected values are fixed
literals independently checked against byte positions. They cover real reader
authentication, decoding, snapshot allocation and cleanup over mocked BLE I/O;
they do not emulate firmware writes or a production command queue.

Off, constant speed, VOC, boost, pause and motor-test operation were observed.
Humidity, light, timer and airing settings were checked without deliberately
activating their environmental/scheduled triggers. Measured RPM can lag a setpoint
or follow another active mode while the constant setting remains unchanged.
Sequential characteristic reads are not an atomic firmware snapshot.

An early run exceeded the harness's cumulative transaction deadline; another
stopped on the airing normalization. Both restored their original settings.
Intermittent read timeouts and slower reads during long sessions were observed;
reads recovered with bounded retry. These tests do not prove fault-free radio
behavior, concurrent control handling, ICE support or completion of the release
checklist. No production integration code, firmware or pairing was changed.


## Authentication and anonymous reads

Further attended checks on SKY firmware `01.01` / hardware `01.00` used the real
reader's authentication, parsing and cleanup through an ESPHome transport adapter.
Each case used a fresh BLE connection. The adapter replaced connection setup,
not authentication or snapshot methods; it did not exercise Bleak route selection.

- Existing-key reads succeeded before and after rejected attempts.
- Two deliberately incorrect-key attempts used a well-formed key in separate checks.
  Each received confirmation `00`, raised `AuthenticationError`, disconnected,
  and performed no metadata/sensor/mode reads or automatic retry.
- Three fresh sessions made no authentication write: before a valid-key read,
  after a valid-key read, and directly after a rejected attempt. All returned
  complete snapshots. All seven mode packets and firmware/hardware/model metadata
  matched adjacent authenticated reads; sensor RPM remained live and plausible.
- Valid reads after rejection preserved the original mode packets. Production
  HA regained ownership and reported fresh constant-speed readings around 1200 rpm.

No AUTH key-characteristic read, physical pairing, key reset or setting write
was performed. Key acquisition is still outside this live acceptance evidence.
These observations establish readable data on this fan in the tested sessions,
not unauthenticated write permission, cold-start behavior, all firmware support
or a new anonymous Home Assistant setup flow.

Automated regressions cover invalid key formats/types at construction,
replacement and direct authentication; copying mutable inputs; connection-time
replacement; rejection/recovery; cancellation and transport failure cleanup;
retry ordering; no input echo in validation errors, and no backend payloads in library logs. Five
mutation/in-flight replacement regressions failed against the preceding code
and pass after the fix. Confirmation policy remains first byte `01`, including
extended replies; empty, zero and unknown first-byte values fail.
