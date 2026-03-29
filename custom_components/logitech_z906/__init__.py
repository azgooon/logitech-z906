"""Logitech Z906 integration — IR-controlled media player via Broadlink."""

import json
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import BROADLINK_DEVICE, CONF_REMOTE_ENTITY, DOMAIN, IR_CODES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = dict(entry.data)

    # Write IR codes to Broadlink storage so remote.send_command can use them
    await _ensure_broadlink_codes(hass, entry.data[CONF_REMOTE_ENTITY])

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _ensure_broadlink_codes(hass: HomeAssistant, remote_entity: str) -> None:
    """Write Z906 IR codes into Broadlink's storage file if not already present."""
    storage_dir = Path(hass.config.path(".storage"))
    for path in storage_dir.glob("broadlink_remote_*_codes"):
        try:
            data = json.loads(path.read_text())
            codes = data.get("data", {})
            if BROADLINK_DEVICE not in codes:
                codes[BROADLINK_DEVICE] = IR_CODES
                path.write_text(json.dumps(data, indent=4))
                _LOGGER.info(
                    "Wrote Z906 IR codes to %s under device '%s'",
                    path.name,
                    BROADLINK_DEVICE,
                )
        except Exception as err:
            _LOGGER.warning("Failed to write IR codes to %s: %s", path.name, err)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
