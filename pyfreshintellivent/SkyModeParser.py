from struct import pack, unpack

from pyfreshintellivent import helpers as h


class SkyModeParser(object):
    def airing_mode_read(value):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<3BH", value)

        enabled = bool(value[0])
        minutes = int(value[2])
        rpm = int(value[3])

        return {
            "enabled": enabled,
            "minutes": minutes,
            "rpm": rpm,
        }

    def airing_mode_write(enabled: bool, minutes: int, rpm: int):
        return pack(
            "<3BH", enabled, 26, h.validated_time(minutes), h.validated_rpm(rpm)
        )

    def boost_read(value):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<B2H", value)

        enabled = bool(value[0])
        rpm = int(value[1])
        seconds = int(value[2])

        return {"enabled": enabled, "seconds": seconds, "rpm": rpm}

    def boost_write(enabled: bool, minutes: int, rpm: int):
        return pack("<2B", enabled, h.validated_time(minutes), h.validated_rpm(rpm))

    def constant_speed_read(value):
        if len(value) != 3:
            raise ValueError(f"Length need to be exactly 3, was {len(value)}.")

        value = unpack("<BH", value)

        enabled = bool(value[0])
        rpm = int(value[1])

        return {"enabled": enabled, "rpm": rpm}

    def constant_speed_write(enabled: bool, rpm: int):
        return pack("<BH", enabled, h.validated_rpm(rpm))

    def humidity_mode_read(self, value):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<BBH", value)

        enabled = bool(value[0])
        detection = int(value[1])
        rpm = int(value[2])

        return {
            "enabled": enabled,
            "detection": detection,
            "detection_description": self.detection_as_string(detection),
            "rpm": rpm,
        }

    def humidity_mode_write(enabled: bool, detection: int, rpm: int):
        return pack(
            "<BBH", enabled, h.validated_detection(detection), h.validated_rpm(rpm)
        )

    def light_and_voc_read(self, value):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<4B", value)

        light_enabled = bool(value[0])
        light_detection = int(value[1])
        voc_enabled = bool(value[2])
        voc_detection = int(value[3])

        return {
            "light": {
                "enabled": light_enabled,
                "detection": light_detection,
                "detection_description": self.detection_as_string(
                    light_detection, False
                ),
            },
            "voc": {
                "enabled": voc_enabled,
                "detection": voc_detection,
                "detection_description": self.detection_as_string(voc_detection),
            },
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
            raise ValueError(f"Length need to be exactly 2, was {len(value)}.")

        value = unpack("<2B", value)

        enabled = bool(value[0])
        minutes = int(value[1])

        return {"enabled": enabled, "minutes": minutes}

    def pause_write(enabled: bool, minutes: int):
        return pack("<2B", enabled, h.validated_time(minutes))

    def temporary_speed_write(enabled: bool, rpm: int):
        return pack("<BH", enabled, h.validated_rpm(rpm))

    def timer_read(value):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<3BH", value)

        minutes = int(value[0])
        delay_enabled = bool(value[1])
        delay_minutes = int(value[2])
        rpm = int(value[3])

        return {
            "delay": {"enabled": delay_enabled, "minutes": delay_minutes},
            "minutes": minutes,
            "rpm": rpm,
        }

    def timer_write(minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int):
        return pack(
            "<3BH",
            minutes,
            delay_enabled,
            delay_minutes,
            h.validated_rpm(rpm),
        )

    def detection_as_string(self, value: int, regular_order: bool = True):
        value = h.validated_detection(value)
        if value == 1:
            return "Low" if regular_order else "High"
        elif value == 2:
            return "Medium"
        elif value == 3:
            return "High" if regular_order else "Low"
        else:
            return "Unknown"
