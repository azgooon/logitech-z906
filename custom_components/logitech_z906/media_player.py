"""Media player platform for Logitech Z906."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CMD_EFFECT,
    CMD_MUTE,
    CMD_OFF,
    CMD_ON,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CONF_POWER_SENSOR,
    CONF_POWER_THRESHOLD,
    CONF_REMOTE_DEVICE,
    CONF_REMOTE_ENTITY,
    DEFAULT_POWER_THRESHOLD,
    DOMAIN,
    SOURCES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Z906 media player from discovery."""
    conf = hass.data[DOMAIN]
    async_add_entities([LogitechZ906(hass, conf)])


class LogitechZ906(RestoreEntity, MediaPlayerEntity):
    """Representation of a Logitech Z906 speaker system."""

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = list(SOURCES.keys())

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self._remote_entity = config[CONF_REMOTE_ENTITY]
        self._remote_device = config[CONF_REMOTE_DEVICE]
        self._power_sensor = config.get(CONF_POWER_SENSOR)
        self._power_threshold = config.get(
            CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD
        )

        self._attr_name = config.get(CONF_NAME, "Logitech Z906")
        self._attr_unique_id = f"logitech_z906_{self._remote_device.lower()}"
        self._attr_state = MediaPlayerState.OFF
        self._attr_source = None
        self._attr_is_volume_muted = False

    async def async_added_to_hass(self) -> None:
        """Restore state and start tracking power sensor."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_source = last_state.attributes.get("source")
            self._attr_is_volume_muted = last_state.attributes.get(
                "is_volume_muted", False
            )

        # Track power sensor for real on/off state
        if self._power_sensor:
            self._update_power_state()
            async_track_state_change_event(
                self.hass, [self._power_sensor], self._power_sensor_changed
            )

    @callback
    def _power_sensor_changed(self, event) -> None:
        """Handle power sensor state change."""
        self._update_power_state()
        self.async_write_ha_state()

    @callback
    def _update_power_state(self) -> None:
        """Update on/off state from power sensor reading."""
        state = self.hass.states.get(self._power_sensor)
        if state is None or state.state in ("unavailable", "unknown"):
            return
        try:
            power = float(state.state)
            self._attr_state = (
                MediaPlayerState.ON
                if power > self._power_threshold
                else MediaPlayerState.OFF
            )
        except (ValueError, TypeError):
            pass

    async def _send_command(self, command: str) -> None:
        """Send an IR command via the Broadlink remote."""
        await self.hass.services.async_call(
            "remote",
            "send_command",
            {
                "entity_id": self._remote_entity,
                "device": self._remote_device,
                "command": command,
            },
        )

    async def async_turn_on(self) -> None:
        """Turn the amplifier on."""
        await self._send_command(CMD_ON)

    async def async_turn_off(self) -> None:
        """Turn the amplifier off."""
        await self._send_command(CMD_OFF)
        self._attr_is_volume_muted = False

    async def async_volume_up(self) -> None:
        """Volume up."""
        await self._send_command(CMD_VOLUME_UP)

    async def async_volume_down(self) -> None:
        """Volume down."""
        await self._send_command(CMD_VOLUME_DOWN)

    async def async_mute_volume(self, mute: bool) -> None:
        """Toggle mute (IR is a toggle, mute param ignored)."""
        await self._send_command(CMD_MUTE)
        self._attr_is_volume_muted = not self._attr_is_volume_muted
        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        command = SOURCES.get(source)
        if command is None:
            _LOGGER.error("Unknown source: %s", source)
            return
        await self._send_command(command)
        self._attr_source = source
        self.async_write_ha_state()
