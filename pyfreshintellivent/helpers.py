def validate_authentication_code(value):
    if value is None:
        print(value)
        raise ValueError('Authentication cannot be empty.')

    # Check if value is valid
    bytes.fromhex(value)

    if len(value) != 8:
        raise ValueError('Authentication code need to be 8 bytes.')
    

def validated_rpm(value):
    if value < 800:
        return 800
    elif value > 2400:
        return 2400
    else:
        return value

def validated_detection(value):
    if value < 0:
        return 0
    elif value > 3:
        return 3
    else:
        return int(value)

def validated_minutes(value):
    if value < 0:
        return 0
    else:
        return int(value)
