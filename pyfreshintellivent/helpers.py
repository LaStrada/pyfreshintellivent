from typing import Union

DETECTION_LOW = "Low"
DETECTION_MEDIUM = "Medium"
DETECTION_HIGH = "High"


def validated_authentication_code(value: Union[bytes, bytearray, str]):
    if value is None:
        raise ValueError("Authentication code cannot be empty.")

    if isinstance(value, str):
        if len(value) != 8:
            raise ValueError(
                f"Authentication code need to be 8 characters, was {len(value)}."
            )
        bytes = bytearray.fromhex(value)
        return bytes

    elif value == bytearray(b"\x00\x00\x00\x00"):
        raise ValueError("Fan was not in pairing mode.")

    elif isinstance(value, (bytes, bytearray)):
        if len(value) != 4:
            raise ValueError(
                f"Authentication code need to be 4 bytes, was {len(value)}."
            )
        return value

    else:
        raise TypeError("Wrong type, expected bytes, bytearray or str.")


def validated_rpm(value: int):
    if value < 800:
        return 800
    elif value > 2400:
        return 2400
    else:
        return value


def validated_detection(value: Union[int, str]):
    if isinstance(value, int):
        if value < 0:
            return 0
        elif value > 3:
            return 3
        else:
            return value
    else:
        if not value.lower() in [
            DETECTION_LOW.lower(),
            DETECTION_MEDIUM.lower(),
            DETECTION_HIGH.lower(),
        ]:
            valid = f"{DETECTION_LOW}, {DETECTION_MEDIUM} and {DETECTION_HIGH}"
            raise ValueError(
                f'"{value}" is not a valid detection type. Valid types are: {valid}.'
            )
        return value


def detection_int_as_string(
    value: int, regular_order: bool = True, disable_low: bool = False
):
    value = validated_detection(value)
    if value == 1:
        if disable_low and regular_order is True:
            return DETECTION_MEDIUM
        return DETECTION_LOW if regular_order else DETECTION_HIGH
    elif value == 2:
        return DETECTION_MEDIUM
    elif value == 3:
        if disable_low and regular_order is False:
            return 2
        return DETECTION_HIGH if regular_order else DETECTION_LOW
    else:
        return "Unknown"


def detection_string_as_int(
    value: str, regular_order: bool = True, disable_low: bool = False
):
    value = validated_detection(value)
    if value.lower() == DETECTION_LOW.lower():
        if disable_low:
            return 2
        else:
            return 1 if regular_order else 3
    elif value.lower() == DETECTION_MEDIUM.lower():
        return 2
    elif value.lower() == DETECTION_HIGH.lower():
        return 3 if regular_order else 1
    else:
        raise ValueError("Invalid detection value")


def validated_time(value: int):
    if value < 0:
        return 0
    else:
        return int(value)


def to_hex(value: Union[bytes, bytearray, str]):
    if isinstance(value, str):
        bytearray.fromhex(value)
        return value
    return "".join("{:02x}".format(x) for x in value)


def to_bytearray(value: Union[bytes, bytearray, str]):
    if isinstance(value, (bytes, bytearray)):
        return value
    elif isinstance(value, str):
        return bytearray.fromhex(value)
    else:
        raise TypeError("Wrong type, expected bytes, bytearray or str.")
