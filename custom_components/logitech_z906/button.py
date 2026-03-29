"""Button platform for Logitech Z906 — one button per IR command."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_REMOTE_ENTITY, DOMAIN, IR_CODES

_LOGGER = logging.getLogger(__name__)

# (key in IR_CODES, display name, icon)
BUTTONS = [
    ("on", "Power On", "mdi:power"),
    ("off", "Power Off", "mdi:power-off"),
    ("volumeUp", "Volume Up", "mdi:volume-plus"),
    ("volumeDown", "Volume Down", "mdi:volume-minus"),
    ("mute", "Mute", "mdi:volume-mute"),
    ("input1", "Input 1", "mdi:numeric-1-box"),
    ("input2", "Input 2", "mdi:numeric-2-box"),
    ("input3", "Input 3", "mdi:numeric-3-box"),
    ("input4", "Input 4", "mdi:numeric-4-box"),
    ("input5", "Input 5", "mdi:numeric-5-box"),
    ("aux", "AUX", "mdi:audio-input-stereo-minijack"),
    ("effect", "Effect", "mdi:surround-sound"),
    ("level", "Level", "mdi:tune-vertical"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Z906 buttons."""
    conf = hass.data[DOMAIN][entry.entry_id]
    remote_entity = conf[CONF_REMOTE_ENTITY]

    async_add_entities(
        [Z906Button(remote_entity, cmd, name, icon) for cmd, name, icon in BUTTONS]
    )


class Z906Button(ButtonEntity):
    """A button that sends one IR command to the Z906."""

    _attr_has_entity_name = True

    def __init__(self, remote_entity: str, command: str, name: str, icon: str) -> None:
        self._remote_entity = remote_entity
        self._command = command
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"logitech_z906_{command}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "logitech_z906")},
            "name": "Logitech Z906",
            "manufacturer": "Logitech",
            "model": "Z906",
        }

    async def async_press(self) -> None:
        """Send the IR command."""
        code = IR_CODES.get(self._command)
        if code is None:
            _LOGGER.error("Unknown command: %s", self._command)
            return
        await self.hass.services.async_call(
            "remote",
            "send_command",
            {
                "entity_id": self._remote_entity,
                "command": "b64:" + code,
            },
        )
