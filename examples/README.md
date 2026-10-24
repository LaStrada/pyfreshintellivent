# Example scripts

Run these commands from the repository root after `poetry install`. Use the
Python versions declared in [package metadata](../pyproject.toml). Device reads
and scans require a nearby supported fan and an available Bluetooth adapter.

## Read a snapshot

```sh
poetry run python examples/read.py --authenticate
```

The script prompts for an existing authentication key without echoing it. It
reads a snapshot, disconnects, then prints operating mode, RPM and the temperature
byte. It does not expose humidity percentage, raw characteristic dumps or settings
controls.

To select a known device, add `--address` with its BLE address or platform UUID.
Without `--authenticate`, the script reads `FRESH_AUTH_CODE` from the environment
if supplied by your credential tooling. Otherwise it attempts an unauthenticated
read. The reader still requires a complete snapshot: if a required characteristic
needs authentication, the read fails instead of returning partial data. Do not
pass a key as a positional argument or paste it into a shell command.

```sh
poetry run python examples/read.py --help
```

A failed read reports the exception type without printing backend payloads.
See [authentication and error handling](../docs/api.md) for details.

## Find a device

```sh
poetry run python examples/scan.py
```

This scans for a supported device and prints its name and address. It exits with
an error if none is found. The smaller `examples/find_device.py` demonstrates the
same scanner helper and prints the returned device object or `None`.

## Troubleshooting

- If no device is found, check power, Bluetooth availability and proximity.
  Close another connected client before trying again.
- If authentication is rejected, check the existing key or use the library's
  documented physical pairing flow. The read example does not pair a device.
- If an import fails, run `poetry install` and invoke the script from the
  repository root with `poetry run`.

Review output before sharing it; scanner output includes device identifiers.
For protocol fields and hardware checks, see the [protocol reference](../characteristics.md)
and [verification guide](../docs/verification.md).
