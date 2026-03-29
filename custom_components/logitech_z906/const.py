"""Constants for the Logitech Z906 integration."""

DOMAIN = "logitech_z906"

CONF_REMOTE_ENTITY = "remote_entity"
CONF_REMOTE_DEVICE = "remote_device"
CONF_POWER_SENSOR = "power_sensor"
CONF_POWER_THRESHOLD = "power_threshold"

DEFAULT_POWER_THRESHOLD = 2

# Broadlink command names (must match keys in Broadlink storage)
CMD_ON = "on"
CMD_OFF = "off"
CMD_MUTE = "mute"
CMD_VOLUME_UP = "volumeUp"
CMD_VOLUME_DOWN = "volumeDown"
CMD_EFFECT = "effect"
CMD_LEVEL = "level"
CMD_NEXT_CHANNEL = "nextChannel"

# Source name -> Broadlink command mapping
SOURCES = {
    "Input 1": "input1",
    "Input 2": "input2",
    "Input 3": "input3",
    "Input 4": "input4",
    "Input 5": "input5",
    "AUX": "aux",
}
