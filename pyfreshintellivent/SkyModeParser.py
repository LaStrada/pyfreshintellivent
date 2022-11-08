from struct import pack, unpack
import helpers as h


def airing_mode_read(value):
    if len(value) != 5:
        raise ValueError("Length need to be exactly 5.")

    value = unpack("<3BH", value)

    enabled = bool(value[0])
    minutes = value[2]
    rpm = value[3]

    return {
        "enabled": enabled,
        "minutes": minutes,
        "rpm": rpm,
    }

def airing_mode_write(enabled: bool, minutes: int, rpm: int):
    return pack( "<3BH", enabled, 26, h.validated_time(minutes), h.validated_rpm(rpm))

def boost_read(value):
    if len(value) != 5:
        raise ValueError("Length need to be exactly 5.")

    value = unpack("<B2H", value)

    enabled = bool(value[0])
    rpm = value[1]
    seconds = value[2]

    return {"enabled": enabled, "seconds": seconds, "rpm": rpm}

def boost_write(enabled: bool, minutes: int, rpm: int):
    return pack("<2B", enabled, h.validated_time(minutes), h.validated_rpm(rpm))

def constant_speed_read(value):
    if len(value) != 3:
        raise ValueError("Length need to be exactly 3.")

    value = unpack("<BH", value)

    enabled = bool(value[0])
    rpm = value[1]

    return {"enabled": enabled, "rpm": rpm}

def constant_speed_write(enabled: bool, rpm: int):
    return pack("<BH", enabled, h.validated_rpm(rpm))

def humidity_mode_read(value):
    if len(value) != 4:
        raise ValueError("Length need to be exactly 4.")

    value = unpack("<BBH", value)

    humidity_enabled = bool(value[0])
    humidity_detection = value[1]
    humidity_rpm = value[2]

    return {
        "enabled": humidity_enabled,
        "detection": humidity_detection,
        "rpm": humidity_rpm,
    }

def humidity_mode_write(enable: bool, detection: int, rpm: int):
    return pack("<BBH", enabled, h.validated_detection(detection), h.validated_rpm(rpm))

def light_and_voc_read(value):
    if len(value) != 4:
        raise ValueError("Length need to be exactly 4.")

    value = unpack("<4B", value)

    light_enabled = bool(value[0])
    light_detection = value[1]
    voc_enabled = bool(value[2])
    voc_detection = value[3]

    return {
        "light": {"enabled": light_enabled, "detection": light_detection},
        "voc": {"enabled": voc_enabled, "detection": voc_detection},
    }

def light_and_voc_write(
    light_enabled: bool, light_detection: int, voc_enabled: bool, voc_detection: int
):
    return pack(
        "<4b",
        bool(light_enabled),
        h.validated_detection(light_detection),
        bool(voc_enabled),
        h.validated_detection(voc_detection),
    )

def pause_read(value):
    if len(value) != 2:
        raise ValueError("Length need to be exactly 2.")

    value = unpack("<2B", value)

    pause_enabled = bool(value[0])
    pause_minutes = value[1]

    return {"enabled": pause_enabled, "minutes": pause_minutes}

def pause_write(enabled: bool, minutes: int):
    return pack("<2B", enabled, h.validated_time(minutes))

def temporary_speed_write(enabled: bool, rpm: int):
    return pack("<BH", enabled, h.validated_rpm(rpm))

def timer_read(value):
    if len(value) != 5:
        raise ValueError("Length need to be exactly 5.")

    value = unpack("<3BH", value)

    timer_runningtime = value[0]
    timer_delay_enabled = bool(value[1])
    timer_delay_minutes = value[2]
    timer_rpm = value[3]

    return {
        "delay": {"enabled": timer_delay_enabled, "minutes": timer_delay_minutes},
        "runTime": timer_runningtime,
        "rpm": timer_rpm,
    }

def timer_write():
