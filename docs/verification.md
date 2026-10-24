# Verification and device support

| Target | Evidence | Current claim |
| --- | --- | --- |
| Fresh Intellivent SKY | Documented packet contract, regression fixtures and user reports | Primary reader target; new lifecycle/auth changes still need live validation |
| Fresh Intellivent ICE / ICE | HACS discovery and 700 RPM reports | Name discovery; reads provisional; no validated ICE write limits |
| Aviant / Pure Sense / Svensa | Related products; model-specific protocol and hardware validation pending | Research candidates, not declared supported |
| Other Fresh products | Same vendor or app alone | Unsupported until protocol and hardware evidence exists |

## Automated verification

CI enforces 100% runtime statement and branch coverage. The current test count
and results are available in the CI run. Tests include cancellation during connect/read/disconnect, repeated
cancellation, bounded cleanup, serialized reads, cancelled lock waiters, retry
exhaustion, real connector callback/deadline composition, backend versus caller
cancellation, transport failures during authentication, negative PIN confirmation,
failed pairing without retaining a key, malformed packets,
all nonzero trigger/motor combinations, VOC round trips and discovery false
positives. The [CI workflow](../.github/workflows/ci.yml) defines the active matrix;
the independent [CI maintenance change](https://github.com/LaStrada/pyfreshintellivent/pull/63)
adds macOS and Windows to the Linux checks.
No simulated test proves physical Bluetooth interoperability.

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

Live hardware acceptance of this rewrite remains pending. Simulated transport
tests do not establish physical interoperability or successful radio recovery.

100% coverage is an enforced regression baseline, not a reliability guarantee.
