# API

## Reader

```python
reader = FreshIntelliventBluetoothDeviceData(
    authentication_code=key,
    max_attempts=3,
    logger=None,
)
result = await reader.update_device(ble_device)
```

`ble_device` is a Bleak `BLEDevice`. The result contains `info`, `sensors` and
`modes` dataclasses. Reuse one reader per fan: it serializes reads and disconnects
between them. Separate readers do not share a lock.

| Argument | Accepted values |
| --- | --- |
| `authentication_code` | Four bytes, a four-byte `bytearray`, eight hex characters, or `None` for anonymous reads. Empty and all-zero keys are rejected. |
| `max_attempts` | Positive integer; use `1` if the caller handles retries. |
| `logger` | Optional `logging.Logger`. |

Assigning `reader.authentication_code` validates the new key immediately and
applies it to the next connection attempt. Invalid assignments leave the previous
key intact; mutable inputs are copied. A rejected key never falls back to anonymous
access. See [authentication verification](verification.md#authentication-and-anonymous-reads).

## Timeouts and retries

| Operation | Deadline |
| --- | --- |
| Connect | 30 seconds |
| Read | 30 seconds per attempt |
| Disconnect | 10 seconds |
| Clear stale characteristic cache | 30 seconds |

Transport errors, unexpected disconnects and connect/read timeouts are retried,
with a one-second delay. These deadlines are separate, not a total operation timeout.
The connector may retry within the connection deadline.

`update_device()` requires device information, status and configuration reads to succeed.
Cancellation waits for disconnect cleanup before releasing the lock.
Authentication rejection, malformed packets and cleanup failures stop retries.
Lower-level `get_*` methods default to best-effort reads and require a connected
client managed by the caller.

## Physical pairing

```python
key = await reader.pair_device(ble_device)
```

Enable pairing on the fan first. This makes one attempt to read and authenticate
the key, read the fan and disconnect. Success returns four key bytes and stores
them on the reader; failure preserves the previous key. Store the key privately.
Physical key acquisition has not yet been tested on hardware.

## Errors

| Exception | Meaning |
| --- | --- |
| `AuthenticationError` | Authentication was rejected. |
| `DisconnectedError` | Connection dropped during a read. |
| `FreshIntelliventTimeoutError` | Connect or read deadline expired. |
| `ConnectionCleanupError` | Disconnect failed; back off before reconnecting. Import from `pyfreshintellivent.exceptions`. |
| `BleakError` | BLE transport failure after retries; does not mean the key is wrong. |
| `TypeError` | Unsupported authentication input type. |
| `ValueError` | Invalid input or malformed packet. |

## Packet encoders

`SkyModeParser` provides `*_read` and `*_write` methods for humidity, light/VOC,
constant speed, timer, airing, pause and boost. `temporary_speed_write()` encodes
motor-test settings.

The write methods return bytes. They do not send settings, confirm changes or
queue commands. See [packet formats and limits](../characteristics.md#configuration-packets).
