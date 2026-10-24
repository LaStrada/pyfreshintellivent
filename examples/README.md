# Example Scripts

This directory contains example scripts demonstrating how to use the pyfreshintellivent library.

## Scripts

### read.py - Full Device Data Reader

Connects to your Fresh Intellivent Sky device and reads all available data including sensors and mode settings.

**Features:**
- Automatic connection management
- Raw BLE data logging for test development
- Optional authentication support
- Full error handling

**Usage:**
```bash
# Without authentication
poetry run python read.py

# With authentication code
poetry run python read.py 6f48b504

# Save raw data to file
poetry run python read.py 6f48b504 > device_data.log 2>&1
```

**Output:**
- Device information (name, firmware, hardware versions)
- Current sensor readings (temperature, humidity, RPM, etc.)
- All mode settings (humidity, timer, boost, etc.)
- Raw BLE characteristic data (for test fixtures)

---

### find_device.py - Device Scanner

Scans for nearby Fresh Intellivent Sky devices and displays their information.

**Usage:**
```bash
poetry run python find_device.py
```

**Output:**
- List of discovered devices
- Device names and addresses
- Signal strength (RSSI)

---

### extract_raw_data.py - Test Fixture Generator

Extracts raw BLE characteristic data from capture logs and formats it as Python test fixtures.

**Usage:**
```bash
# From a log file
python extract_raw_data.py device_data.log

# From stdin
cat device_data.log | python extract_raw_data.py

# Direct pipe
poetry run python read.py 6f48b504 2>&1 | python extract_raw_data.py
```

**Output:**
- Python test fixtures (copy-paste ready)
- Markdown table format
- Byte length information

**Example output:**
```python
# Test fixtures extracted from real device
DEVICE_STATUS_SAMPLE = bytes.fromhex("00007601400af8000000400a001c00")
HUMIDITY_SAMPLE = bytes.fromhex("0103d007")
TIMER_SAMPLE = bytes.fromhex("3c0105d007")
```

## Workflow: Capture Device Data for Testing

1. **Capture raw data from your device:**
   ```bash
   poetry run python read.py YOUR_AUTH_CODE > device_data.log 2>&1
   ```

2. **Extract test fixtures:**
   ```bash
   python extract_raw_data.py device_data.log > test_fixtures.py
   ```

3. **Use in your tests:**
   ```python
   # Import the fixtures
   from test_fixtures import DEVICE_STATUS_SAMPLE, HUMIDITY_SAMPLE
   
   # Use in tests
   def test_device_status_parsing():
       sensor_data = SensorData.from_bytes(DEVICE_STATUS_SAMPLE)
       assert sensor_data.temperature == 22.0
   ```

## Requirements

All scripts require:
- Python 3.12+
- Fresh Intellivent Sky device nearby (except extract_raw_data.py)
- Bluetooth enabled
- Poetry environment activated

## Troubleshooting

### "No device found"
- Ensure the device is powered on
- Check Bluetooth is enabled
- Verify device is within range (< 10 meters)
- Confirm device name is "Intellivent SKY"

### "Authentication failed"
- Verify authentication code is correct (8 hex characters)
- Try running without auth code first
- Check if device actually requires authentication

### "Module not found"
Run from the project root with poetry:
```bash
cd /path/to/pyfreshintellivent
poetry install
poetry run python examples/read.py
```

## More Information

For detailed instructions on raw data capture and usage, see:
- [RAW_DATA_INSTRUCTIONS.md](../RAW_DATA_INSTRUCTIONS.md) - Comprehensive guide
- [README.md](../README.md) - Library documentation
- [docs/](../docs/) - API reference
