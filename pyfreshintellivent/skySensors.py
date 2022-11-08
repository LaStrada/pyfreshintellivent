from struct import unpack


class SkySensors(object):
    def __init__(self, data: bytearray):
        if data is None or len(data) != 15:
            raise ValueError(f"Length of object need to be 15, was {len(data)}.")

        values = unpack("<2B5HBH", data)

        self._values = values

        self.status = bool(values[0])
        self.mode = values[1]
        self.rpm = values[5]
        self.mode_description = "Unknown"

        if self.mode == 0:
            self.mode_description = "Off"
        elif self.mode == 6:
            self.mode_description = "Pause"
        elif self.mode == 16:
            self.mode_description = "Constant speed"
        elif self.mode == 34:
            self.mode_description = "Light"
        elif self.mode == 49:
            self.mode_description = "Humidity"
        elif self.mode == 52:
            self.mode_description = "VOC"
        elif self.mode == 103:
            self.mode_description = "Boost"
        else:
            self.mode_description = "Unknown"

    def as_dict(self):
        return {
            "status": self.status,
            "mode": {
                "description": self.mode_description,
                "raw_value": self.mode,
            },
            "rpm": self.rpm,
        }
