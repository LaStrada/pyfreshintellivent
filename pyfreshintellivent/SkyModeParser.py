from struct import pack, unpack

class SkyModeParser:
    def airing_mode(value):
        if len(value) != 5:
            raise ValueError("Length need to be exactly 5.")

        value = unpack("<3BH", value)

        airing_enabled = bool(value[0])
        airing_run_time = value[2]
        airing_rpm = value[3]

        return {
            "enabled": airing_enabled,
            "runTime": airing_run_time,
            "rpm": airing_rpm,
        }
    
    def boost(value):
        if len(value) != 5:
            raise ValueError("Length need to be exactly 5.")
        
        value = unpack("<B2H", value)

        boost_enabled = bool(value[0])
        boost_rpm = value[1]
        boost_seconds = value[2]

        return {"enabled": boost_enabled, "seconds": boost_seconds, "rpm": boost_rpm}
    
    def constant_speed(value):
        if len(value) != 3:
            raise ValueError("Length need to be exactly 3.")

        value = unpack("<BH", value)

        constant_speed_enabled = bool(value[0])
        constant_speed_rpm = value[1]

        return {"enabled": constant_speed_enabled, "rpm": constant_speed_rpm}
    
    def humidity_mode(value):
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
    
    def light_and_voc(value):
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
    
    def pause(value):
        if len(value) != 2:
            raise ValueError("Length need to be exactly 2.")

        value = unpack("<2B", value)

        pause_enabled = bool(value[0])
        pause_minutes = value[1]

        return {"enabled": pause_enabled, "minutes": pause_minutes}
    
    def timer(value):
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