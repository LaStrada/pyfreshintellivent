def validate_authentication_code(value: str):
    if value is None:
        raise ValueError("Authentication cannot be empty.")

    # Check if value is valid
    bytes.fromhex(value)

    if len(value) != 8:
        raise ValueError("Authentication code need to be 8 bytes.")

    return True


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
