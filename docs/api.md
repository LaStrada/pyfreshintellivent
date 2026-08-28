# API Reference

Complete API documentation for pyfreshintellivent.

## Main Classes

### `FreshIntelliventBluetoothDeviceData`

The main class for reading device data with automatic connection management.

#### Constructor

```python
FreshIntelliventBluetoothDeviceData(
    logger: logging.Logger | None = None,
    max_attempts: int = 3,
    authentication_code: bytes | bytearray | str | None = None
)
```

**Parameters:**
- `logger` (optional): Custom logger instance for debugging
- `max_attempts` (default: 3): Number of connection retry attempts on transient failures
- `authentication_code` (optional): Authentication code for protected devices

**Example:**
```python
from pyfreshintellivent import FreshIntelliventBluetoothDeviceData

# Basic usage
parser = FreshIntelliventBluetoothDeviceData()

# With authentication
parser = FreshIntelliventBluetoothDeviceData(
    authentication_code="your_code_here"
)

# With custom settings
import logging
logger = logging.getLogger(__name__)
parser = FreshIntelliventBluetoothDeviceData(
    logger=logger,
    max_attempts=5,
    authentication_code="code"
)
```

#### Methods

##### `update_device(ble_device: BLEDevice) -> FreshIntelliventDevice`

Reads all device data with automatic connection management.

**Parameters:**
- `ble_device`: A `BLEDevice` instance from bleak scanner

**Returns:**
- `FreshIntelliventDevice`: Complete device data (typed)

**Raises:**
- `DisconnectedError`: Device disconnected during operation
- `AuthenticationError`: Authentication failed
- `FreshIntelliventError`: General error
- `FreshIntelliventTimeoutError`: Operation timed out (30 seconds)
- `UnsupportedDeviceError`: Device not supported

**Features:**
- Automatically connects to device
- Authenticates if code provided
- Reads all device information
- Reads all sensor data
- Reads all mode settings
- Automatically disconnects
- Retries on transient failures
- Timeout protection (30 seconds)
- Always closes connection, even on errors

**Example:**
```python
from bleak import BleakScanner
from pyfreshintellivent import FreshIntelliventBluetoothDeviceData

# Find device
ble_device = await BleakScanner.find_device_by_name("Intellivent SKY")

# Read all data
parser = FreshIntelliventBluetoothDeviceData()
device = await parser.update_device(ble_device)

# Access data
print(f"Temperature: {device.sensors.temperature}°C")
print(f"Humidity: {device.sensors.humidity}%")
```

---

## Data Models

### `FreshIntelliventDevice`

Complete device information container.

**Attributes:**
- `name: str | None` - Device name
- `address: str | None` - Bluetooth MAC address
- `manufacturer: str | None` - Manufacturer name (usually "Fresh")
- `model: str` - Device model (default: "Intellivent Sky")
- `hw_version: str | None` - Hardware version
- `sw_version: str | None` - Software version
- `fw_version: str | None` - Firmware version
- `sensors: SensorData` - All sensor readings
- `modes: DeviceModes` - All mode settings

**Example:**
```python
device = await parser.update_device(ble_device)

print(f"Device: {device.name}")
print(f"Address: {device.address}")
print(f"Firmware: {device.fw_version}")
```

### `SensorData`

Current sensor readings from the device.

**Attributes:**
- `temperature: float | None` - Temperature in Celsius
- `humidity: float | None` - Relative humidity (0-100%)
- `rpm: int | None` - Current fan speed in RPM
- `mode: str | None` - Current operating mode
- `status: bool | None` - Device status
- `authenticated: bool | None` - Whether device is authenticated

**Example:**
```python
sensors = device.sensors

if sensors.temperature:
    print(f"Temperature: {sensors.temperature}°C")

if sensors.humidity:
    print(f"Humidity: {sensors.humidity}%")
    
if sensors.rpm:
    print(f"Fan speed: {sensors.rpm} RPM")
```

### `DeviceModes`

Container for all device mode settings.

**Attributes:**
- `humidity: HumidityMode | None` - Humidity-based control
- `light_and_voc: LightAndVocMode | None` - Light and VOC sensor control
- `constant_speed: ConstantSpeedMode | None` - Constant speed mode
- `timer: TimerMode | None` - Timer mode
- `airing: AiringMode | None` - Airing mode
- `pause: PauseMode | None` - Pause mode
- `boost: BoostMode | None` - Boost mode

**Example:**
```python
modes = device.modes

# Check if mode is enabled
if modes.humidity:
    print(f"Humidity mode: {modes.humidity.detection}")
    print(f"RPM: {modes.humidity.rpm}")

if modes.boost:
    print(f"Boost enabled: {modes.boost.enabled}")
```

---

## Mode Data Models

### `HumidityMode`

Humidity-based automatic control.

**Attributes:**
- `enabled: bool` - Whether mode is enabled
- `detection: str` - Detection level: "Low", "Medium", "High"
- `detection_raw: int` - Raw detection value
- `rpm: int` - Fan speed in RPM when triggered

**Example:**
```python
if device.modes.humidity:
    mode = device.modes.humidity
    print(f"Enabled: {mode.enabled}")
    print(f"Sensitivity: {mode.detection}")
    print(f"Speed: {mode.rpm} RPM")
```

### `LightAndVocMode`

Light and VOC (Volatile Organic Compounds) sensor control.

**Attributes:**
- `light: LightSettings` - Light sensor settings
- `voc: VocSettings` - VOC sensor settings

#### `LightSettings`
- `enabled: bool` - Whether light sensor is enabled
- `detection: str` - Detection level: "Low", "Medium", "High"
- `detection_raw: int` - Raw detection value

#### `VocSettings`
- `enabled: bool` - Whether VOC sensor is enabled
- `detection: str` - Detection level: "Low", "Medium", "High"
- `detection_raw: int` - Raw detection value

**Example:**
```python
if device.modes.light_and_voc:
    mode = device.modes.light_and_voc
    
    print(f"Light enabled: {mode.light.enabled}")
    print(f"Light sensitivity: {mode.light.detection}")
    
    print(f"VOC enabled: {mode.voc.enabled}")
    print(f"VOC sensitivity: {mode.voc.detection}")
```

### `ConstantSpeedMode`

Fixed fan speed mode.

**Attributes:**
- `enabled: bool` - Whether mode is enabled
- `rpm: int` - Fixed fan speed in RPM

**Example:**
```python
if device.modes.constant_speed:
    mode = device.modes.constant_speed
    print(f"Constant speed: {mode.rpm} RPM")
```

### `TimerMode`

Timed operation with optional delay.

**Attributes:**
- `delay: DelaySettings` - Delay before starting
- `minutes: int` - Timer duration in minutes
- `rpm: int` - Fan speed in RPM during timer

#### `DelaySettings`
- `enabled: bool` - Whether delay is enabled
- `minutes: int` - Delay duration in minutes

**Example:**
```python
if device.modes.timer:
    mode = device.modes.timer
    
    if mode.delay.enabled:
        print(f"Delay: {mode.delay.minutes} minutes")
    
    print(f"Duration: {mode.minutes} minutes")
    print(f"Speed: {mode.rpm} RPM")
```

### `AiringMode`

Scheduled airing mode.

**Attributes:**
- `enabled: bool` - Whether mode is enabled
- `minutes: int` - Duration in minutes
- `rpm: int` - Fan speed in RPM

**Example:**
```python
if device.modes.airing:
    mode = device.modes.airing
    print(f"Airing: {mode.minutes}min @ {mode.rpm} RPM")
```

### `PauseMode`

Temporarily pause operation.

**Attributes:**
- `enabled: bool` - Whether pause is active
- `minutes: int` - Pause duration in minutes

**Example:**
```python
if device.modes.pause:
    mode = device.modes.pause
    if mode.enabled:
        print(f"Paused for {mode.minutes} minutes")
```

### `BoostMode`

High-speed boost mode.

**Attributes:**
- `enabled: bool` - Whether boost is active
- `seconds: int` - Boost duration in seconds
- `rpm: int` - Boost fan speed in RPM

**Example:**
```python
if device.modes.boost:
    mode = device.modes.boost
    if mode.enabled:
        print(f"Boost: {mode.seconds}s @ {mode.rpm} RPM")
```

---

## Exceptions

All exceptions inherit from `FreshIntelliventError`.

### `FreshIntelliventError`

Base exception for all library errors.

**Usage:**
```python
from pyfreshintellivent import FreshIntelliventError

try:
    device = await parser.update_device(ble_device)
except FreshIntelliventError as e:
    print(f"Error: {e}")
```

### `DisconnectedError`

Raised when device disconnects unexpectedly during operation.

**Common causes:**
- Device went out of range
- Device was powered off
- Connection interference

**Usage:**
```python
from pyfreshintellivent import DisconnectedError

try:
    device = await parser.update_device(ble_device)
except DisconnectedError:
    print("Device disconnected - try moving closer")
```

### `AuthenticationError`

Raised when authentication fails.

**Common causes:**
- Wrong authentication code
- Device requires authentication but none provided

**Usage:**
```python
from pyfreshintellivent import AuthenticationError

try:
    parser = FreshIntelliventBluetoothDeviceData(
        authentication_code="wrong_code"
    )
    device = await parser.update_device(ble_device)
except AuthenticationError:
    print("Authentication failed - check code")
```

### `FreshIntelliventTimeoutError`

Raised when operation times out (30 seconds).

**Common causes:**
- Device not responding
- Very slow connection
- Too much interference

**Usage:**
```python
from pyfreshintellivent import FreshIntelliventTimeoutError

try:
    device = await parser.update_device(ble_device)
except FreshIntelliventTimeoutError:
    print("Operation timed out - device may be unresponsive")
```

### `UnsupportedDeviceError`

Raised when device is not a Fresh Intellivent Sky.

**Usage:**
```python
from pyfreshintellivent import UnsupportedDeviceError

try:
    device = await parser.update_device(ble_device)
except UnsupportedDeviceError:
    print("This is not a Fresh Intellivent Sky device")
```

---

## Complete Example

```python
import asyncio
from bleak import BleakScanner
from pyfreshintellivent import (
    FreshIntelliventBluetoothDeviceData,
    FreshIntelliventError,
    DisconnectedError,
    AuthenticationError,
)

async def main():
    # Find device
    ble_device = await BleakScanner.find_device_by_name("Intellivent SKY")
    if not ble_device:
        print("Device not found")
        return
    
    # Create parser with optional authentication
    parser = FreshIntelliventBluetoothDeviceData(
        # authentication_code="your_code_here"  # Uncomment if needed
    )
    
    # Read all data
    try:
        device = await parser.update_device(ble_device)
    except DisconnectedError:
        print("Device disconnected")
        return
    except AuthenticationError:
        print("Authentication failed")
        return
    except FreshIntelliventError as e:
        print(f"Error: {e}")
        return
    
    # Display device information
    print(f"Device: {device.name}")
    print(f"Firmware: {device.fw_version}")
    
    # Display sensor data
    print(f"\nSensors:")
    print(f"  Temperature: {device.sensors.temperature}°C")
    print(f"  Humidity: {device.sensors.humidity}%")
    print(f"  RPM: {device.sensors.rpm}")
    
    # Display mode settings
    if device.modes.humidity:
        print(f"\nHumidity Mode:")
        print(f"  Enabled: {device.modes.humidity.enabled}")
        print(f"  Detection: {device.modes.humidity.detection}")
        print(f"  RPM: {device.modes.humidity.rpm}")

asyncio.run(main())
```
