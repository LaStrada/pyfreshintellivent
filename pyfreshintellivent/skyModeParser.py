from struct import pack, unpack
from typing import Union

from . import helpers as h


class SkyModeParser(object):
    def airing_read(self, value: Union[bytes, bytearray]):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<?2BH", value)

        enabled = bool(value[0])
        minutes = h.validated_time(int(value[2]))
        rpm = int(value[3])

        return {
            "enabled": enabled,
            "minutes": minutes,
            "rpm": rpm,
        }

    def airing_write(self, enabled: bool, minutes: int, rpm: int):
        return pack(
            "<?2BH", enabled, 26, h.validated_time(minutes), h.validated_rpm(rpm)
        )

    def boost_read(self, value: Union[bytes, bytearray]):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")
        value = unpack("<?2H", value)

        enabled = bool(value[0])
        rpm = int(value[1])
        seconds = int(value[2])

        return {"enabled": enabled, "seconds": seconds, "rpm": rpm}

    def boost_write(self, enabled: bool, rpm: int, seconds: int):
        val = pack("<?2H", enabled, h.validated_rpm(rpm), h.validated_time(seconds))
        return val

    def constant_speed_read(self, value: Union[bytes, bytearray]):
        if len(value) != 3:
            raise ValueError(f"Length need to be exactly 3, was {len(value)}.")
        value = unpack("<?H", value)

        enabled = bool(value[0])
        rpm = int(value[1])

        return {"enabled": enabled, "rpm": rpm}

    def constant_speed_write(self, enabled: bool, rpm: int):
        return pack("<?H", enabled, h.validated_rpm(rpm))

    def humidity_read(self, value: Union[bytes, bytearray]):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<?BH", value)

        enabled = bool(value[0])
        detection = int(value[1])
        rpm = int(value[2])

        return {
            "enabled": enabled,
            "detection": h.detection_int_as_string(detection),
            "detection_raw": detection,
            "rpm": rpm,
        }

    def humidity_write(self, enabled: bool, detection: str, rpm: int):
        return pack(
            "<?BH", enabled, h.detection_string_as_int(detection), h.validated_rpm(rpm)
        )

    def light_and_voc_read(self, value: Union[bytes, bytearray]):
        if len(value) != 4:
            raise ValueError(f"Length need to be exactly 4, was {len(value)}.")

        value = unpack("<?B?B", value)

        light_enabled = bool(value[0])
        light_detection = int(value[1])
        voc_enabled = bool(value[2])
        voc_detection = int(value[3])

        return {
            "light": {
                "enabled": light_enabled,
                "detection": h.detection_int_as_string(
                    value=light_detection, disable_low=True
                ),
                "detection_raw": light_detection,
            },
            "voc": {
                "enabled": voc_enabled,
                "detection": h.detection_int_as_string(
                    value=voc_detection, regular_order=False
                ),
                "detection_raw": voc_detection,
            },
        }

    def light_and_voc_write(
        self,
        light_enabled: bool,
        light_detection: str,
        voc_enabled: bool,
        voc_detection: str,
    ):
        return pack(
            "<?B?B",
            bool(light_enabled),
            h.detection_string_as_int(light_detection),
            bool(voc_enabled),
            h.detection_string_as_int(voc_detection),
        )

    def pause_read(self, value: Union[bytes, bytearray]):
        if len(value) != 2:
            raise ValueError(f"Length need to be exactly 2, was {len(value)}.")

        value = unpack("<?B", value)

        enabled = bool(value[0])
        minutes = int(value[1])

        return {"enabled": enabled, "minutes": minutes}

    def pause_write(self, enabled: bool, minutes: int):
        return pack("<?B", enabled, h.validated_time(minutes))

    def temporary_speed_write(self, enabled: bool, rpm: int):
        return pack("<?H", enabled, h.validated_rpm(rpm))

    def timer_read(self, value: Union[bytes, bytearray]):
        if len(value) != 5:
            raise ValueError(f"Length need to be exactly 5, was {len(value)}.")

        value = unpack("<B?BH", value)

        minutes = int(value[0])
        delay_enabled = bool(value[1])
        delay_minutes = int(value[2])
        rpm = int(value[3])

        return {
            "delay": {"enabled": delay_enabled, "minutes": delay_minutes},
            "minutes": minutes,
            "rpm": rpm,
        }

    def timer_write(
        self, minutes: int, delay_enabled: bool, delay_minutes: int, rpm: int
    ):
        return pack(
            "<B?BH",
            minutes,
            delay_enabled,
            delay_minutes,
            h.validated_rpm(rpm),
        )
