"""Constants for Fresh Intellivent Sky devices."""

# Device identification
DEVICE_NAME = "Intellivent SKY"
DEVICE_MODEL = "Intellivent Sky"

# Connection and update settings
UPDATE_TIMEOUT = 30.0  # Timeout for update operations in seconds
DEFAULT_MAX_UPDATE_ATTEMPTS = 3  # Number of retry attempts for connections

# Parser dictionary keys - used by parser methods and device data extraction
KEY_ENABLED = "enabled"
KEY_DETECTION = "detection"
KEY_DETECTION_RAW = "detection_raw"
KEY_RPM = "rpm"
KEY_MINUTES = "minutes"
KEY_SECONDS = "seconds"
KEY_LIGHT = "light"
KEY_VOC = "voc"
KEY_DELAY = "delay"
