# Verification and device support

| Target | Evidence | Current claim |
| --- | --- | --- |
| Fresh Intellivent SKY | Documented packet contract, regression fixtures and user reports | Primary reader target; new lifecycle/auth changes still need live validation |
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

Hardware acceptance of the current reader remains pending. Record completed
checks with the tested model, firmware and transport before expanding support.
