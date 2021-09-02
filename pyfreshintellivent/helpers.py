def validatedRPM(value):
    if value < 800:
        return 800
    elif value > 2400:
        return 2400
    else:
        return value


def validatedDetection(value):
    if value < 0:
        return 0
    elif value > 3:
        return 3
    else:
        return int(value)


def validatedMinutes(value):
    if value < 0:
        return 0
    else:
        return int(value)
