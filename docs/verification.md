# Device support and testing

| Device | Status |
| --- | --- |
| Intellivent SKY | Reads tested on hardware; see remaining gaps below. |
| Intellivent ICE / ICE | Recognized by name; protocol compatibility unverified. |
| Other Fresh products | Unsupported. |

## Tested on SKY

- Authenticated reads, rejected keys and recovery with a valid key.
- Repeated reads, reconnects, HA entry reload and disable/enable.
- Individual and consecutive setting changes, readback and retention after reconnect.
- Off, constant speed, VOC, boost, pause and motor-test states.

Setting changes were tested with a separate harness. The library itself provides
packet encoders, not a device-control API.

## Remaining hardware tests

- Physical pairing and key acquisition.
- Temperature accuracy and calibration of raw humidity, VOC and light readings.
- Humidity, light, timer and airing trigger activation.
- Cancellation, proxy failover, competing clients and HA restart recovery.
- Other device revisions and ICE.

## Authentication and anonymous reads

Anonymous reads worked on new connections before and after authentication or
rejection. Access after a fan cold start and anonymous writes remain untested.
Pairing has automated tests only.

## Readback behavior

- Boost counts down in seconds; pause took precedence over boost.
- A requested five-minute airing period read back as fifteen minutes.
- Light/VOC updates preserved the other setting. Airing updates preserved its
  cycle period; constant-speed updates preserved the enabled flag.
- Consecutive writes retained the final setting. Mode and RPM can lag behind
  stored settings; confirm readback before reporting a change as applied.

## Automated tests

Tests enforce 100% statement and branch coverage. They cover packet decoding,
authentication, retries, cancellation and cleanup. Recorded packets are replayed
with mocked BLE in [hardware snapshot tests](../tests/test_hardware_snapshots.py).
See [CI](../.github/workflows/ci.yml) for tested Python versions and platforms.
