"""Errors reported by the Fresh Intellivent library."""


class FreshIntelliventError(Exception):
    """Base exception for Fresh Intellivent errors."""


class DisconnectedError(FreshIntelliventError):
    """Device disconnected unexpectedly."""


class AuthenticationError(FreshIntelliventError):
    """Authentication failed."""


class UnsupportedDeviceError(FreshIntelliventError):
    """Device is not supported."""


class FreshIntelliventTimeoutError(FreshIntelliventError):
    """Timeout exception for Fresh Intellivent errors."""


class ConnectionCleanupError(FreshIntelliventError):
    """Connection state is uncertain; automatic reconnect must stop."""
