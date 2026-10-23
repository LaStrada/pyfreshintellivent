# Verification and device support

| Target | Evidence | Current claim |
| --- | --- | --- |
| Fresh Intellivent SKY | Two Android app protocols, historical captures and user reports | Primary reader target; new lifecycle/auth changes still need live validation |
| Fresh Intellivent ICE / ICE | HACS discovery and 700 RPM reports, same app family | Name discovery; reads provisional; no validated ICE write limits |
| Aviant / Pure Sense / Svensa | Grouped with SKY family in Fresh Connect | Research candidates, not declared supported |
| Other Fresh products | Same vendor or app alone | Unsupported until protocol and hardware evidence exists |

## Automated verification

As of the initial protocol follow-up: 403 tests and 100% runtime statement/branch
coverage. Tests include cancellation during connect/read/disconnect, repeated
cancellation, bounded cleanup, serialized reads, cancelled lock waiters, retry
exhaustion, transport failures, negative PIN confirmation, malformed packets,
all nonzero trigger/motor combinations, VOC round trips and discovery false
positives. CI adds Python 3.12–3.14 and simulated transport behavior on three OSes.
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

The owner's overnight test on 2026-10-24 could not proceed: the fan was powered
but absent from advertisements on seven HA scanners, while other BLE traffic
continued. No live write test or successful recovery is claimed. The outage
started before the HA 2026.10.3 update, so update timing does not establish cause.

100% coverage is an enforced regression baseline, not a reliability guarantee.
