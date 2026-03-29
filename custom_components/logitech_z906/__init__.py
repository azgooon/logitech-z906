"""Logitech Z906 integration — IR-controlled media player via Broadlink."""

import voluptuous as vol

from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_POWER_SENSOR,
    CONF_POWER_THRESHOLD,
    CONF_REMOTE_DEVICE,
    CONF_REMOTE_ENTITY,
    DEFAULT_POWER_THRESHOLD,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_REMOTE_ENTITY): cv.entity_id,
                vol.Required(CONF_REMOTE_DEVICE): cv.string,
                vol.Optional(CONF_POWER_SENSOR): cv.entity_id,
                vol.Optional(
                    CONF_POWER_THRESHOLD, default=DEFAULT_POWER_THRESHOLD
                ): vol.Coerce(float),
                vol.Optional(CONF_NAME, default="Logitech Z906"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [Platform.MEDIA_PLAYER]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Logitech Z906 integration from YAML."""
    if DOMAIN not in config:
        return True

    hass.data[DOMAIN] = config[DOMAIN]

    await hass.helpers.discovery.async_load_platform(
        Platform.MEDIA_PLAYER, DOMAIN, {}, config
    )

    return True
