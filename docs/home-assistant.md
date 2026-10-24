# Home Assistant integration roadmap

The first Core submission should be a small, authenticated, read-only integration
written against the reader API. Start with SKY and manually initiated setup.
Require a config flow that tests the key against the device, supports
reauthentication, and prevents duplicate entries by Bluetooth address. Use HA's Bluetooth manager and fresh device lookup
on every poll so local adapters and ESPHome proxies work through the same API.

Expose RPM, operating mode and the device-reported temperature as enabled
sensors. Temperature uses the dedicated byte at offset 13; its sensor location
and accuracy relative to a room thermometer remain unverified. Do not expose
humidity or label raw VOC/light as physical units. Failed reads must make sensors unavailable rather than preserve a fresh
success timestamp with stale data. Use one coordinator and one reader per entry.
Unload and cancellation must release the session.

A compatible library package must be published and its hardware acceptance
completed before an upstream integration can pin it. Integration tests need
manual selection, authentication failures/reauth, duplicate prevention, setup
retry, update failure/recovery, sensor values and unload behavior. Follow Core's
current quality scale, generated manifests/translations and documentation process.

## Later automatic discovery

Automatic Bluetooth discovery and its config-flow tests belong in a separate,
small follow-up Core PR. This is a plan only; keep it out of the initial
submission. Bluetooth transport and manually initiated setup remain part of the
initial design.

## Later controls

A `fan` entity implies direct on/off or speed semantics that this mode-based device
does not consistently provide. Prefer switches for persistent enabled flags,
numbers for durations/RPM limits and selects for detection levels. A timed boost
may need an entity action with parameters; a button only suits a fixed preset.
On the checked SKY firmware, active boost reads return remaining seconds.
Keep a requested duration separate from that countdown; confirm behavior on other
firmware before choosing entity semantics.

A plain FIFO of complete stale packets is insufficient. A per-device transaction
lock must cover read-current → merge requested fields → write → read back. Preserve
unmodified fields, especially constant-speed enabled. Serialize overlapping changes
and polls; bounded coalescing can combine pending fields with explicit last-write
rules. Confirmed state comes from readback. If a write times out, reconcile by
reading before retrying: a timeout does not mean the device rejected the write.
Do not silently drop newer changes or clear pending work after a failed write.
Entities must not assemble complete packets from a client captured during setup.
A completion may clear only its own pending command, never one queued during an
await. Keep queues per config entry, refresh running status after writes, and
separate configured setpoints from measured RPM or the currently active trigger.
Regression tests must include commands arriving during write/readback awaits,
interleaved sibling fields, idempotent edits, two-device isolation, normalization,
and uncertain outcomes without blindly restarting timed modes.

A final independent phase can add unauthenticated read-only setup after its actual
capabilities and missing fields have been verified across firmware versions.
