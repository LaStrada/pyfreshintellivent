# API and lifecycle

## Reader

`FreshIntelliventBluetoothDeviceData(logger=None, max_attempts=3, authentication_code=None)`
accepts a four-byte key or eight hexadecimal characters. Invalid and all-zero
keys fail before connecting. One reader should be reused per physical device;
its lock does not coordinate independent readers, processes, HA instances or a
phone app.

`await reader.update_device(ble_device)` returns `FreshIntelliventDevice` with
`info`, `sensors` and `modes` dataclasses. Obtain `ble_device` from the caller's
Bluetooth transport. Home Assistant integrations must use HA Bluetooth APIs,
not start a second scanner.

Every attempt has a 30-second connection deadline and a separate 30-second
read deadline. Disconnect has a 10-second deadline. Cache invalidation after a
missing characteristic has a 30-second deadline. Retry delay is one second;
`max_attempts=1` is appropriate when the caller already schedules retries.
The retry connector may perform transport retries inside the connection deadline.

Unexpected disconnects, read deadlines and Bleak transport errors are retried
within the configured limit. Authentication rejection, malformed packets and
cleanup failures are not blindly retried. Required characteristic reads are
strict: a transport failure cannot return an apparently successful partial
snapshot. Individual `get_*` methods default to diagnostic, best-effort reads;
they are lower-level APIs and require the caller to own a connected client.

Cancellation during connect cleans up the partially established client.
Cancellation during a read waits for bounded disconnect cleanup before releasing
the lock and propagating `CancelledError`. A backend can still ignore cancellation
or fail to release a physical connection; application deadlines are not proof of
radio recovery. If cleanup fails after a retryable read failure, a
`ConnectionCleanupError` stops reconnect attempts. It is available from
`pyfreshintellivent.exceptions` and is a `FreshIntelliventError`.

## Physical pairing

`await reader.pair_device(ble_device)` reads the four-byte key while the user has
enabled pairing on the fan, authenticates with its confirmation characteristic,
validates a complete snapshot, and disconnects. Only then does it return immutable
key bytes and retain the key for subsequent reads. A zero key, negative
confirmation, bad packet, transport error, cancellation or failed cleanup leaves
the reader's previous key unchanged. Pairing uses the same lock as polling and
makes one attempt; it does not trigger physical pairing or reset the fan.

Store the returned key in the caller's private credential/config-entry storage;
do not log it. A HA flow can offer this as its normal authenticated setup path,
with an existing-key field for migration and recovery.

## Errors

- `AuthenticationError`: invalid/rejected authentication exchange; prompt to
  check the key or pair again, rather than repeatedly retrying a bad key.
- `DisconnectedError`: connection dropped while reading.
- `FreshIntelliventTimeoutError`: connection/read deadline expired.
- `ConnectionCleanupError`: disconnect could not be confirmed; caller should
  back off and investigate instead of immediately opening another connection.
- `BleakError`: transport failure after attempts are exhausted.
- `ValueError`: invalid input or malformed response; firmware/protocol evidence
  is needed before widening packet acceptance.

Exceptions can carry chained backend errors. Do not forward raw tracebacks,
credentials, addresses or private transport details without reviewing/redacting.

## Encoders

`SkyModeParser` has paired `*_read` / `*_write` methods for existing setting
packets. `*_write` returns bytes only. There is no transaction queue, optimistic
state handling or device write-confirmation API in this reader release.
See [the packet table and limitations](../characteristics.md).
