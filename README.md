[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/pyfreshintellivent.svg)](https://badge.fury.io/py/pyfreshintellivent)
![Linting](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/linting.yml/badge.svg)
![Tests](https://github.com/LaStrada/pyfreshintellivent/actions/workflows/tests.yml/badge.svg)

# pyfreshintellivent

Modern, type-safe Python interface for Fresh Intellivent Sky bathroom ventilation fan using Bluetooth Low Energy.

## ✨ Features

- 🔒 **Type-safe**: Full type hints and IDE autocomplete support
- 🔄 **Automatic connection management**: No more hanging connections
- 🛡️ **Robust error handling**: Automatic retries and proper cleanup
- 📊 **Typed data models**: All sensor readings and modes are strongly typed
- 🚀 **Modern async/await**: Built on latest asyncio patterns
- 🔐 **Authentication support**: Optional authentication for protected devices

## 📋 Requirements

- Python 3.12 or higher
- Bluetooth 4.0+ adapter

## 📦 Installation

```bash
pip install pyfreshintellivent
```

## 🚀 Quick Start

```python
import asyncio
from bleak import BleakScanner
from pyfreshintellivent import FreshIntelliventBluetoothDeviceData

async def main():
    # Find device
    device = await BleakScanner.find_device_by_name("Intellivent SKY")
    
    # Create parser
    parser = FreshIntelliventBluetoothDeviceData()
    
    # Read all data (connection is automatically managed)
    fresh_device = await parser.update_device(device)
    
    # Access typed data with full IDE support
    print(f"Temperature: {fresh_device.sensors.temperature}°C")
    print(f"Humidity: {fresh_device.sensors.humidity}%")
    print(f"RPM: {fresh_device.sensors.rpm}")
    
    # Access mode settings
    if fresh_device.modes.humidity:
        mode = fresh_device.modes.humidity
        print(f"Humidity mode: {mode.detection}, RPM: {mode.rpm}")

asyncio.run(main())
```

## 📖 Documentation

- **[API Reference](docs/api.md)** - Complete API documentation
- **[Examples](examples/)** - Working code examples

### Examples

- `python examples/scan.py` — quick one-shot scan that prints the first matching device (10s timeout).
- `python examples/read.py [--address AA:BB:CC:DD:EE:FF] [--auth CODE]` — read all data; accepts an optional BLE address/UUID to skip the picker and an optional auth code for protected devices.

## 🔐 Authentication

For devices that require authentication:

```python
parser = FreshIntelliventBluetoothDeviceData(
    authentication_code="your_code_here"
)
device = await parser.update_device(ble_device)
```

## 🧪 Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linters
poetry run ruff check pyfreshintellivent
poetry run mypy pyfreshintellivent
poetry run pylint pyfreshintellivent
```

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. All tests pass
2. Code is typed (mypy passes)
3. Linting passes (ruff, pylint)
4. Add tests for new features

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE.md)

## 🔗 Related Projects

- [Fresh Intellivent Sky integration for Home Assistant](https://github.com/angoyd/freshintelliventHacs)

## 🙏 Credits

Created and maintained by the community. Special thanks to all contributors!
