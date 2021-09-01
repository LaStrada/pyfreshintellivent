def validatedRPM(self, value):
    if value < 800:
        return 800
    elif value > 2400:
        return 2400
    else:
        return value

def validatedDetection(self, value):
    if value < 0:
        return 0
    elif value > 3:
        return 3
    else:
        return int(value)

def validatedMinutes(self, value):
    if value < 0:
        return 0
    else:
        return int(value)

def bytesToString(self, value):
    return

def stringToBytes(self, value):
    return binascii.b2a_hex(value).decode('utf-8')
