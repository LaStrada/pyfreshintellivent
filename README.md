# pyfreshintellivent

[![CI](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/ci.yml/badge.svg)](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/ci.yml)

Async Bluetooth reader for Fresh Intellivent SKY. Each read connects to the fan,
returns a complete snapshot of its sensors and settings, and releases the
connection. Concurrent reads on the same reader are serialized.

The reader API replaces the legacy `FreshIntelliVent` connection/write API.
Existing callers need to follow the [migration guide](docs/migration.md).
This documentation describes the current source; for an installed package, use
its release-tag documentation.

## Read a fan

From the repository root:

```sh
poetry install
poetry run python examples/read.py --authenticate
```

The script prompts for an existing authentication key without echoing it.
Use `--address` to select a known fan. See [examples](examples/README.md) for
scanning and [pairing](docs/api.md#physical-pairing) to obtain a key.

For application code, this example reads the key from `FRESH_AUTH_CODE`, supplied
by your credential tooling:

```python
import asyncio
import os

from pyfreshintellivent import FreshIntelliventBluetoothDeviceData
from pyfreshintellivent.scanner import scan


async def main() -> None:
    device = await scan(timeout=10)
    if device is None:
        raise RuntimeError("No supported fan discovered")
    reader = FreshIntelliventBluetoothDeviceData(
        authentication_code=os.environ["FRESH_AUTH_CODE"],
        max_attempts=1,
    )
    snapshot = await reader.update_device(device)
    print(f"RPM: {snapshot.sensors.rpm}, mode: {snapshot.sensors.mode}")


asyncio.run(main())
```

Reuse one reader per device for repeated polling. Applications that manage
Bluetooth themselves can pass their own `BLEDevice`; Home Assistant integrations
should obtain it through HA's Bluetooth manager.

## Supported features

- SKY sensor and configuration reads, authenticated reads and physical pairing.
- RPM, operating mode, device-reported temperature, raw sensor fields and
  configuration models.
- Name-based SKY and ICE discovery. ICE reads remain provisional; see the
  [device support and verification guide](docs/verification.md).
- Configuration packet encoders in `SkyModeParser`. These return bytes;
  the library does not send or confirm setting changes.

Humidity percentage is unavailable: `humidity_raw`, `voc_raw` and `light_raw`
have no validated conversion to physical units. Temperature uses the dedicated
protocol field; sensor placement and measurement accuracy remain unverified.
See the [protocol reference](characteristics.md) for services, characteristics
and packet layouts, and the [verification matrix](docs/verification.md) for
software-tested versus hardware-verified capabilities.

## Documentation

- [API, pairing and error handling](docs/api.md)
- [Migration from the legacy API](docs/migration.md)
- [Bluetooth protocol](characteristics.md)
- [Device support and hardware verification](docs/verification.md)
- [Development, checks and releases](docs/development.md)

Supported Python versions are declared in [package metadata](pyproject.toml).

Licensed under [Apache 2.0](LICENSE.md).
