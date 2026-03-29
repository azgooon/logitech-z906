"""Media player platform for Logitech Z906."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    BROADLINK_DEVICE,
    CONF_POWER_SENSOR,
    CONF_REMOTE_ENTITY,
    DOMAIN,
    IR_CODES,
    POWER_THRESHOLD,
    SOURCES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Z906 media player from a config entry."""
    conf = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LogitechZ906(hass, conf)])


class LogitechZ906(RestoreEntity, MediaPlayerEntity):
    """Representation of a Logitech Z906 speaker system."""

    _attr_has_entity_name = True
    _attr_name = None
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
        self._power_sensor = config.get(CONF_POWER_SENSOR)

        self._attr_unique_id = "logitech_z906"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "logitech_z906")},
            "name": "Logitech Z906",
            "manufacturer": "Logitech",
            "model": "Z906",
        }
        self._attr_state = MediaPlayerState.OFF
        self._attr_source = None
        self._attr_is_volume_muted = False
        self._power_watts = None

    async def async_added_to_hass(self) -> None:
        """Restore state and start tracking power sensor."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_source = last_state.attributes.get("source")
            self._attr_is_volume_muted = last_state.attributes.get(
                "is_volume_muted", False
            )

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

    @property
    def extra_state_attributes(self) -> dict | None:
        """Expose power consumption when sensor is configured."""
        if self._power_watts is not None:
            return {"power_consumption": self._power_watts}
        return None

    @callback
    def _update_power_state(self) -> None:
        """Update on/off state from power sensor reading."""
        state = self.hass.states.get(self._power_sensor)
        if state is None or state.state in ("unavailable", "unknown"):
            return
        try:
            power = float(state.state)
            self._power_watts = power
            self._attr_state = (
                MediaPlayerState.ON
                if power > POWER_THRESHOLD
                else MediaPlayerState.OFF
            )
        except (ValueError, TypeError):
            pass

    @property
    def _is_on(self) -> bool:
        """Check if amplifier is currently on based on power sensor."""
        if self._power_sensor:
            return self._attr_state == MediaPlayerState.ON
        return self._attr_state == MediaPlayerState.ON

    async def _send_ir(self, command: str) -> None:
        """Send an IR command via the configured remote using embedded base64 codes."""
        code = IR_CODES.get(command)
        if code is None:
            _LOGGER.error("Unknown IR command: %s", command)
            return
        await self.hass.services.async_call(
            "remote",
            "send_command",
            {
                "entity_id": self._remote_entity,
                "command": "b64:" + code,
            },
        )

    async def async_turn_on(self) -> None:
        """Turn the amplifier on. Skip if already on (prevents redundant IR)."""
        if self._is_on:
            return
        await self._send_ir("on")
        if not self._power_sensor:
            self._attr_state = MediaPlayerState.ON
            self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the amplifier off. Skip if already off (prevents redundant IR)."""
        if not self._is_on:
            return
        await self._send_ir("off")
        self._attr_is_volume_muted = False
        if not self._power_sensor:
            self._attr_state = MediaPlayerState.OFF
            self.async_write_ha_state()

    async def async_volume_up(self) -> None:
        """Volume up."""
        await self._send_ir("volumeUp")

    async def async_volume_down(self) -> None:
        """Volume down."""
        await self._send_ir("volumeDown")

    async def async_mute_volume(self, mute: bool) -> None:
        """Toggle mute."""
        await self._send_ir("mute")
        self._attr_is_volume_muted = not self._attr_is_volume_muted
        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Select input source using discrete IR codes."""
        command = SOURCES.get(source)
        if command is None:
            _LOGGER.error("Unknown source: %s", source)
            return
        await self._send_ir(command)
        self._attr_source = source
        self.async_write_ha_state()
