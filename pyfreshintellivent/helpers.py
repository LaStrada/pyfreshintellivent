from typing import Union

DETECTION_LOW = "LOW"
DETECTION_MEDIUM = "MEDIUM"
DETECTION_HIGH = "HIGH"


def validated_authentication_code(value: Union[bytes, bytearray, str]):
    if value is None:
        raise ValueError("Authentication cannot be empty.")

    if isinstance(value, str):
        if len(value) != 8:
            raise ValueError(
                f"Authentication code need to be 8 characters, was {len(value)}."
            )
        bytes = bytearray.fromhex(value)
        return bytes

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
        if not value.upper() in [DETECTION_LOW, DETECTION_MEDIUM, DETECTION_HIGH]:
            valid = f"{DETECTION_LOW}, {DETECTION_MEDIUM} and {DETECTION_HIGH}"
            raise ValueError(
                f'"{value}" is not a valid detection type. Valid types are: {valid}.'
            )
        return value


def detection_int_as_string(value: int, regular_order: bool = True):
    value = validated_detection(value)
    if value == 1:
        return "Low" if regular_order else "High"
    elif value == 2:
        return "Medium"
    elif value == 3:
        return "High" if regular_order else "Low"
    else:
        return "Unknown"


def detection_string_as_int(value: str, regular_order: bool = True):
    value = validated_detection(value)
    if value.upper() == DETECTION_LOW:
        return 1 if regular_order else 3
    elif value.upper() == DETECTION_MEDIUM:
        return 2
    elif value.upper() == DETECTION_HIGH:
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
