# pyfreshintellivent

[![CI](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/ci.yml/badge.svg)](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/ci.yml)

Async Bluetooth reader for Fresh Intellivent SKY sensors and settings.

The reader API replaces the legacy `FreshIntelliVent` connection/write API.
Existing callers need to follow the [migration guide](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/migration.md).

## Read a fan

From the repository root:

```sh
poetry install
poetry run python examples/read.py --authenticate
```

The script prompts for an existing authentication key without echoing it.
Use `--address` to select a known fan. See [examples](https://github.com/LaStrada/pyfreshintellivent/blob/main/examples/README.md) for
scanning and [pairing](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/api.md#physical-pairing) to obtain a key.

In application code:

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
    result = await reader.update_device(device)
    print(f"RPM: {result.sensors.rpm}, mode: {result.sensors.mode}")


asyncio.run(main())
```

Reuse one reader per device for repeated polling. Applications that manage
Bluetooth themselves can pass their own `BLEDevice`; Home Assistant integrations
should obtain it through HA's Bluetooth manager.

## Supported features

- SKY sensor and configuration reads with an existing authentication key.
- RPM, operating mode, device-reported temperature, raw sensor fields and
  configuration models.
- Name-based SKY and ICE discovery. ICE reads remain provisional; see the
  [device support](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/verification.md).
- Configuration packet encoders in `SkyModeParser`. These return bytes;
  the library does not send or confirm setting changes.

Humidity percentage is unavailable: `humidity_raw`, `voc_raw` and `light_raw`
have no validated conversion to physical units. Temperature uses the dedicated
protocol field; sensor placement and measurement accuracy remain unverified.
See the [protocol reference](https://github.com/LaStrada/pyfreshintellivent/blob/main/characteristics.md) for services, characteristics
and packet layouts.

## Documentation

- [API, pairing and error handling](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/api.md)
- [Migration from the legacy API](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/migration.md)
- [Bluetooth protocol](https://github.com/LaStrada/pyfreshintellivent/blob/main/characteristics.md)
- [Device support and hardware verification](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/verification.md)
- [Development](https://github.com/LaStrada/pyfreshintellivent/blob/main/docs/development.md)

Supported Python versions are declared in [package metadata](https://github.com/LaStrada/pyfreshintellivent/blob/main/pyproject.toml).

Licensed under [Apache 2.0](https://github.com/LaStrada/pyfreshintellivent/blob/main/LICENSE.md).
