"""Helper functions for Fresh Intellivent Sky devices."""

from typing import Union

DETECTION_LOW = "Low"
DETECTION_MEDIUM = "Medium"
DETECTION_HIGH = "High"


def validated_authentication_code(value: Union[bytes, bytearray, str]) -> bytearray:
    """Validate authentication code input."""
    if value is None:
        raise ValueError("Authentication code cannot be empty.")

    if isinstance(value, str):
        if len(value) != 8:
            raise ValueError(
                f"Authentication code need to be 8 characters, was {len(value)}."
            )
        return bytearray.fromhex(value)

    if value == bytearray(b"\x00\x00\x00\x00"):
        raise ValueError("Fan was not in pairing mode.")

    if isinstance(value, (bytes, bytearray)):
        if len(value) != 4:
            raise ValueError(
                f"Authentication code need to be 4 bytes, was {len(value)}."
            )
        return bytearray(value)

    raise TypeError("Wrong type, expected bytes, bytearray or str.")


def validated_rpm(value: int) -> int:
    """Validate RPM input."""
    if value < 800:
        return 800
    if value > 2400:
        return 2400
    return value


def validated_detection(value: Union[int, str]) -> int:
    """Validate detection input."""
    if isinstance(value, int):
        if value < 0:
            return 0
        if value > 3:
            return 3
        return value
    if value.lower() == DETECTION_LOW.lower():
        return 1
    if value.lower() == DETECTION_MEDIUM.lower():
        return 2
    if value.lower() == DETECTION_HIGH.lower():
        return 3
    valid = f"{DETECTION_LOW}, {DETECTION_MEDIUM} and {DETECTION_HIGH}"
    raise ValueError(
        f'"{value}" is not a valid detection type. Valid types are: {valid}.'
    )


def detection_int_as_string(
    value: int, regular_order: bool = True, disable_low: bool = False
) -> str:
    """Convert detection integer to string representation."""
    validated_value = validated_detection(value)
    assert isinstance(validated_value, int)
    value = validated_value
    if value == 1:
        if disable_low and regular_order is True:
            return DETECTION_MEDIUM
        return DETECTION_LOW if regular_order else DETECTION_HIGH
    if value == 2:
        return DETECTION_MEDIUM
    if value == 3:
        if disable_low and regular_order is False:
            return DETECTION_MEDIUM
        return DETECTION_HIGH if regular_order else DETECTION_LOW
    return "Unknown"


def detection_string_as_int(
    value: str, regular_order: bool = True, disable_low: bool = False
) -> int:
    """Convert detection string to integer representation."""
    validated_detection(value)
    if value.casefold() == DETECTION_LOW.casefold():
        if disable_low:
            return 2
        return 1 if regular_order else 3
    if value.casefold() == DETECTION_MEDIUM.casefold():
        return 2
    if value.casefold() == DETECTION_HIGH.casefold():
        return 3 if regular_order else 1
    raise ValueError("Invalid detection value")


def validated_time(value: int) -> int:
    """Validate time input."""
    if value < 0:
        return 0
    return int(value)


def to_bytearray(value: Union[bytes, bytearray, str]) -> bytearray:
    """Convert a value to bytearray."""
    if isinstance(value, (bytes, bytearray)):
        return bytearray(value)
    if isinstance(value, str):
        return bytearray.fromhex(value)
    raise TypeError("Wrong type, expected bytes, bytearray or str.")
