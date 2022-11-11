from typing import Union


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


def validated_detection(value: int):
    if value < 0:
        return 0
    elif value > 3:
        return 3
    else:
        return int(value)


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
