class SkySensors(object):
    def __init__(self, data):
        if data is None or len(data) != 9:
            raise ValueError("Length of object need to be 9.")

        self._data = data

        self.status = bool(data[0])
        self.mode = data[1]
        self.rpm = data[5]
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
