# Verification and device support

Hardware evidence currently covers one Intellivent SKY reporting model `40`,
firmware `01.01` and hardware `01.00`. It does not establish compatibility with
other revisions.

| Device | Support boundary |
| --- | --- |
| Fresh Intellivent SKY | Reader and packet encoders implemented; hardware observations below apply to the tested revision |
| Fresh Intellivent ICE / ICE | Name discovery implemented; reads provisional; write limits unverified |
| Other Fresh products | Unsupported until protocol and hardware evidence is available |

## Verification matrix

| Capability | Implemented and automated | Observed on SKY hardware | Still unverified |
| --- | --- | --- | --- |
| Sensor fields and units | RPM, mode and temperature fields decoded; raw humidity, VOC and light values retained | Captured field values and observed mode/RPM changes | Temperature sensor placement/calibration; relative-humidity, VOC-concentration and lux conversions |
| Complete snapshots | Status and seven mode packets decoded; malformed frames rejected; earlier snapshots remain independent | Complete reads, repeated reconnects and retained settings | Other firmware and ICE packet compatibility |
| Existing-key authentication | Input validation, defensive copying, rejection, cleanup and recovery | Valid-key reads; incorrect keys rejected without further reads; valid reads recovered | Behavior across other device revisions |
| Anonymous reads | `None` skips authentication and key acquisition | Complete reads on fresh connections before and after authenticated or rejected attempts | Cold-start behavior; anonymous writes |
| Pairing | Key acquisition, confirmation and failure cleanup tested with simulated BLE | No physical pairing or key acquisition tested | Physical pairing acceptance |
| Settings retention | Encoders, shared fields and recorded readback snapshots tested | Individual fields, ordered and interleaved changes, reconnect retention and the final result of back-to-back writes | Concurrent controls and a production command queue |
| Active modes | Trigger decoding and recorded transient packets tested | Off, constant speed, VOC, boost, pause and motor test | Humidity, light, timer and airing trigger activation |
| Connection lifecycle | Deadlines, retries, cancellation and cleanup failures tested with isolated transports | Repeated reads and reconnects; development HA polling, entry reload and disable/enable | Hardware cancellation, proxy loss/failover, phone contention and controlled HA restart |

Settings changes used a separate test harness making acknowledged GATT writes.
The library provides packet encoders, but no supported device-write API or command
queue. These observations do not validate HA control entities.

## Observed SKY semantics

- Boost duration counts down in seconds. With boost and pause both enabled, the
  reported active trigger was pause. Pause alone reported zero RPM. Behavior
  after pause expiry remains unverified.
- An airing request for 5 minutes read back as 15 minutes, with sibling fields
  unchanged. This is a firmware observation, not a universal minimum or an
  encoder clamp. Controls must publish confirmed readback rather than assume
  an acknowledged request was stored unchanged.
- Light and VOC share a characteristic; changing either setting retained the
  other. Constant-speed enablement and RPM remained independent, and airing
  updates preserved the cycle-period field.
- Cumulative settings survived a reconnect. Back-to-back writes retained the
  final requested setting; this does not show that every intermediate speed
  was physically reached.
- Measured RPM can lag a setting or follow another active mode. Sequential
  characteristic reads are not an atomic firmware snapshot. Intermittent read
  timeouts occurred and bounded retries recovered; reliable software cleanup
  does not guarantee fault-free radio behavior.

## Authentication and anonymous reads

Keys must be four bytes or eight hexadecimal characters representing four bytes;
an all-zero key is rejected. Invalid formats and types are rejected before BLE I/O. Mutable
inputs are copied, and replacing a configured key affects the next connection
attempt rather than an attempt already connecting. Confirmation follows the
existing first-byte contract: `01` succeeds, including extended replies; empty
replies and other first-byte values fail.

Anonymous reads succeeded in the tested fresh connections, including directly
after rejection. They did not read the key characteristic or alter settings.
This establishes neither anonymous write permission nor access after a cold
start. Pairing and key acquisition have automated coverage only. No anonymous
Home Assistant setup flow is implied by these observations.

## Automated verification

The suite enforces 100% runtime statement and branch coverage. It covers packet
formats, discovery, authentication boundaries, serialized reads, retries,
deadlines, cancellation, connector callbacks and cleanup failures.

The [hardware snapshot tests](../tests/test_hardware_snapshots.py) replay
[sanitized captures](../tests/fixtures/sky_hardware_snapshots.json) through real
reader decoding and lifecycle code with mocked BLE I/O. Fixed expectations
cover complete snapshots, independent nested state, retained sibling fields and
observed normalization. Separate transient captures test sensor decoding without
inventing simultaneous settings snapshots. The
[authentication regressions](../tests/test_authentication_regressions.py) cover
input handling, key replacement, rejection/recovery and cleanup.

See the [CI workflow](../.github/workflows/ci.yml) for the active Python/platform
matrix. Coverage measures exercised software paths, not physical compatibility.

## Hardware acceptance before release

Record model, firmware, app version, transport and date without credentials.
For each target revision:

1. Verify cold-start reads, valid and rejected keys, and physical pairing as
   separate cases. Check that credentials never appear in logs.
2. Check repeated polls, overlapping callers and cancellation during connection
   and reads; verify a subsequent read succeeds with no retained connection.
3. Exercise HA unload/reload and controlled restart, proxy loss/failover and
   phone-app contention without a retry loop or stale device reference.
4. Compare sensor values and active triggers with the app. Do not infer humidity
   percentages or physical units for raw fields without evidence.
5. For future controls, save the original settings, change one field, confirm
   readback and preserve sibling fields. Exercise ordered and overlapping
   requests, then restore in `finally` and verify through a fresh connection.
