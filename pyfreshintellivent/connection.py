"""Cancellation-safe cleanup for a single BLE connection."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache

from .exceptions import ConnectionCleanupError

DISCONNECT_TIMEOUT = 10.0
_LOGGER = logging.getLogger(__name__)


@dataclass
class ConnectionState:
    """Retain cleanup failure across connector retries and timeout boundaries."""

    cleanup_error: BaseException | None = None


async def disconnect(
    client: BleakClient, *, connection_state: ConnectionState | None = None
) -> None:
    """Finish bounded cleanup before propagating cancellation to the caller."""
    caller_task = asyncio.current_task()
    assert caller_task is not None
    initial_cancellations = caller_task.cancelling()

    async def cleanup() -> None:
        async with asyncio.timeout(DISCONNECT_TIMEOUT):
            await client.disconnect()

    task = asyncio.create_task(cleanup())
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            # Shield also raises when the cleanup task itself was cancelled.
            if caller_task.cancelling() > initial_cancellations:
                cancelled = True
        except Exception:  # pylint: disable=broad-exception-caught
            # Retrieve the original backend error below.
            break
    try:
        task.result()
    except BaseException as err:
        if connection_state is not None:
            connection_state.cleanup_error = err
        if isinstance(err, asyncio.CancelledError):
            raise ConnectionCleanupError(
                "Disconnect was cancelled before completion"
            ) from err
        raise
    finally:
        if cancelled:
            raise asyncio.CancelledError


class ClientWithCleanup(BleakClientWithServiceCache):
    """Close a partial connection when the connector has not returned it yet."""

    def __init__(
        self,
        address_or_ble_device: BLEDevice | str,
        disconnected_callback: Callable[[BleakClient], None] | None = None,
        *,
        connection_state: ConnectionState | None = None,
        **kwargs: Any,
    ) -> None:
        self._connection_state = connection_state or ConnectionState()
        self._disconnect_callback = disconnected_callback
        self._connection_phase: Literal["idle", "connecting", "connected"] = "idle"
        self._disconnected_during_connect = False
        super().__init__(
            address_or_ble_device,
            disconnected_callback=self._on_disconnect,
            **kwargs,
        )

    def _on_disconnect(self, client: BleakClient) -> None:
        """Forward disconnects only for an attempt that actually connected."""
        if self._connection_phase == "connecting":
            self._disconnected_during_connect = True
        elif self._connection_phase == "connected":
            self._connection_phase = "idle"
            if self._disconnect_callback is not None:
                self._disconnect_callback(client)

    async def connect(self, **kwargs: Any) -> None:
        if self._connection_state.cleanup_error is not None:
            raise ConnectionCleanupError(
                "Failed to close partial connection"
            ) from self._connection_state.cleanup_error
        self._connection_phase = "connecting"
        self._disconnected_during_connect = False
        try:
            await super().connect(**kwargs)
        except BaseException as primary_error:
            # Ignore notifications while cleaning up a failed attempt.
            self._connection_phase = "idle"
            try:
                await disconnect(self, connection_state=self._connection_state)
            except Exception as err:  # pylint: disable=broad-exception-caught
                self._connection_state.cleanup_error = err
                _LOGGER.warning("Connection cleanup failed (%s)", type(err).__name__)
                if not isinstance(primary_error, asyncio.CancelledError):
                    raise ConnectionCleanupError(
                        "Failed to close partial connection"
                    ) from primary_error
            raise
        self._connection_phase = "connected"
        if self._disconnected_during_connect:
            # Do not hide a real disconnect just before connect() returned.
            self._on_disconnect(self)
