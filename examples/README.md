# Examples

Run from the repository root after `poetry install`.

## Read a fan

```sh
poetry run python examples/read.py --authenticate
```

Prompts for an existing key without displaying it, then prints mode, RPM and the
temperature field. Add `--address` to select a known BLE address or platform UUID.

Without `--authenticate`, the script uses `FRESH_AUTH_CODE` if set; otherwise it
attempts an anonymous read. It does not pair the fan or change settings.

```sh
poetry run python examples/read.py --help
```

## Find a fan

```sh
poetry run python examples/scan.py
```

Prints the device name and address. If no fan is found, check Bluetooth, distance
and whether another client is connected.

See the [API reference](../docs/api.md) for authentication and errors.
