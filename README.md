# pyfreshintellivent

[![CI](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/ci.yml/badge.svg)](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/ci.yml)

Async Bluetooth reader for Fresh Intellivent SKY. Python 3.12–3.14.

**This branch contains the unreleased 1.0.0b1 rewrite.** It is incompatible with
0.3.x and must not replace the library underneath an existing HACS integration.
No 1.0 package has been published by this work.

The reader connects, optionally authenticates, reads a complete snapshot and
releases the connection. Concurrent reads on the same reader are serialized.
Retries and disconnect cleanup are bounded, including cancellation during startup
or shutdown. This reduces software-side connection leaks; it cannot recover a
powered fan whose Bluetooth radio has stopped advertising.

## Read a fan

```sh
poetry install
poetry run python examples/read.py --authenticate
```

The example prompts for an existing authentication key without echoing it. An
address can be selected with `--address`; secrets should not be command-line
arguments. Integrators may obtain a `BLEDevice` from Home Assistant's Bluetooth
manager, including an ESPHome proxy, and pass it to the reader.

```python
import os
from pyfreshintellivent import FreshIntelliventBluetoothDeviceData
from pyfreshintellivent.scanner import scan

async def read_fan():
    device = await scan(timeout=10)
    if device is None:
        raise RuntimeError("No supported fan discovered")
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code=os.environ["FRESH_AUTH_CODE"],
        max_attempts=1,
    )
    snapshot = await reader.update_device(device)
    return snapshot.sensors.rpm, snapshot.sensors.mode
```

## What is supported

- SKY sensor and configuration reads, with optional four-byte authentication and
  explicit PIN confirmation.
- RPM, operating mode, temperature byte, raw sensor values and configuration models.
- Name-based discovery for SKY and ICE. ICE is a protocol candidate supported by
  community reports, **not hardware-validated by this rewrite**.
- Existing configuration encoders in `SkyModeParser`. They generate bytes; they do
  not execute, queue or confirm setting changes.

There is **no humidity percentage**. Its previous conversion had no established
basis. `humidity_raw`, `voc_raw` and `light_raw` have no calibrated physical units.
Temperature comes from byte 13; the old temperature field actually decoded VOC.
See the [protocol evidence](characteristics.md) before presenting readings to users.

## Documentation

- [API and connection behavior](docs/api.md)
- [Migration from 0.3.x and earlier rewrite snapshots](docs/migration.md)
- [Protocol and source evidence](characteristics.md)
- [Device support and verification matrix](docs/verification.md)
- [Home Assistant roadmap and controls design](docs/home-assistant.md)
- [Development and release checks](docs/development.md)

## Development

```sh
poetry install
poetry run pytest
poetry run black --check pyfreshintellivent tests
poetry run isort --check-only pyfreshintellivent tests
poetry run ruff check pyfreshintellivent tests
poetry run mypy pyfreshintellivent
poetry run pylint pyfreshintellivent
poetry build
```

CI requires 100% runtime statement and branch coverage. It tests all supported
Python versions, runs transport simulations on Linux/macOS/Windows, and validates
an installed wheel. Coverage does not establish firmware correctness or replace
physical-device testing.

Licensed under [Apache 2.0](LICENSE.md).
