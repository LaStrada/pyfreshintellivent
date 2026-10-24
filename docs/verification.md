# Verification and device support

| Target | Evidence | Current claim |
| --- | --- | --- |
| Fresh Intellivent SKY | Packet contract, regression fixtures and a live SKY check | Existing-key reads, two scheduled polls and HA entry reload/disable-enable verified on one fan; broader acceptance pending |
| Fresh Intellivent ICE / ICE | HACS discovery and 700 RPM reports | Name discovery; reads provisional; no validated ICE write limits |
| Other Fresh products | Same vendor or app alone | Unsupported until protocol and hardware evidence exists |

## Automated verification

The test suite enforces 100% runtime statement and branch coverage. It covers:

- Connection/read/disconnect cancellation, deadlines and cleanup failures.
- Serialized reads, cancelled lock waiters, retries and connector callbacks.
- Authentication rejection, transport failures and failed pairing.
- Malformed packets, trigger/motor combinations, setting round trips and discovery.

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
Physical pairing, wrong-key rejection, ten-poll/overlapping-call stress tests,
cancellation during BLE operations, proxy loss/failover, phone contention and
sensor comparison with the app remain unverified on hardware. App version was
not recorded because no app comparison was performed. No control entity or
supported device-write API was exercised by the dev integration. Other firmware
and ICE support still require separate validation.
