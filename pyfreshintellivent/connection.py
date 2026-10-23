"""Cancellation-safe cleanup for a single BLE connection."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import BleakClientWithServiceCache

from .exceptions import ConnectionCleanupError

DISCONNECT_TIMEOUT = 10.0
_LOGGER = logging.getLogger(__name__)


async def disconnect(client: BleakClient) -> None:
    """Finish bounded cleanup before propagating cancellation to the caller."""

    async def cleanup() -> None:
        async with asyncio.timeout(DISCONNECT_TIMEOUT):
            await client.disconnect()

    task = asyncio.create_task(cleanup())
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
        except Exception:  # pylint: disable=broad-exception-caught
            # Retrieve the original backend error below.
            break
    try:
        task.result()
    finally:
        if cancelled:
            raise asyncio.CancelledError


class ClientWithCleanup(BleakClientWithServiceCache):
    """Close a partial connection when the connector has not returned it yet."""

    async def connect(self, **kwargs: Any) -> None:
        try:
            await super().connect(**kwargs)
        except BaseException as primary_error:
            try:
                await disconnect(self)
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOGGER.warning("Connection cleanup failed (%s)", type(err).__name__)
                if not isinstance(primary_error, asyncio.CancelledError):
                    raise ConnectionCleanupError(
                        "Failed to close partial connection"
                    ) from primary_error
            raise
