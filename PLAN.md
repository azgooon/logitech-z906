# Logitech Z906 Custom Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A custom HA integration that exposes the Logitech Z906 as a media_player entity, controlled via IR through a Broadlink remote.

**Architecture:** YAML-configured integration with a single media_player entity. Sends IR commands via `remote.send_command` to an existing Broadlink entity. Power state from an energy monitoring sensor, all other state assumed. Restore state for source/mute persistence across restarts.

**Tech Stack:** Home Assistant custom component (Python), Broadlink integration (dependency), ESPHome power sensor (dependency)

---

## File Structure

```
custom_components/logitech_z906/
  __init__.py          # Platform setup, YAML config schema
  manifest.json        # Integration metadata
  media_player.py      # Media player entity (all logic here)
  const.py             # Domain name, command map, source list
```

All files in `custom_components/logitech_z906/` within the repo root. The repo IS the custom component — clone/symlink it into `/config/custom_components/logitech_z906/` on HA.

---

### Task 1: Constants and manifest

**Files:**
- Create: `custom_components/logitech_z906/const.py`
- Create: `custom_components/logitech_z906/manifest.json`

- [ ] **Step 1: Create const.py**

```python
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
```

- [ ] **Step 2: Create manifest.json**

```json
{
  "domain": "logitech_z906",
  "name": "Logitech Z906",
  "codeowners": ["@azgooon"],
  "dependencies": ["remote"],
  "documentation": "https://github.com/azgooon/logitech-z906",
  "iot_class": "assumed_state",
  "issue_tracker": "https://github.com/azgooon/logitech-z906/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

- [ ] **Step 3: Commit**

```bash
git add custom_components/logitech_z906/const.py custom_components/logitech_z906/manifest.json
git commit -m "feat: add constants and manifest"
```

---

### Task 2: Integration setup

**Files:**
- Create: `custom_components/logitech_z906/__init__.py`

- [ ] **Step 1: Create __init__.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/logitech_z906/__init__.py
git commit -m "feat: add integration setup with YAML config"
```

---

### Task 3: Media player entity

**Files:**
- Create: `custom_components/logitech_z906/media_player.py`

This is the main file — the entity that appears in HA.

- [ ] **Step 1: Create media_player.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/logitech_z906/media_player.py
git commit -m "feat: add media player entity with IR control and state tracking"
```

---

### Task 4: Deploy and test on HA

**Files:**
- Modify: HA's `/config/configuration.yaml` (add integration config)

- [ ] **Step 1: Copy component to HA**

```bash
sshpass -p 'Azgon13170' ssh hassio@192.168.4.10 "sudo mkdir -p /config/custom_components/logitech_z906"

for f in __init__.py const.py manifest.json media_player.py; do
  sshpass -p 'Azgon13170' ssh hassio@192.168.4.10 "sudo cp /dev/stdin /config/custom_components/logitech_z906/$f" < custom_components/logitech_z906/$f
done
```

- [ ] **Step 2: Add configuration to HA**

Append to `/config/configuration.yaml`:

```yaml
logitech_z906:
  remote_entity: remote.broadlink_rm_pro_remote
  remote_device: Logitech
  power_sensor: sensor.amplifier_plug_power
  power_threshold: 2
```

- [ ] **Step 3: Restart HA and verify**

```bash
# Restart HA
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "http://192.168.4.10:8123/api/services/homeassistant/restart"

# After restart, check entity exists
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://192.168.4.10:8123/api/states/media_player.logitech_z906" | python3 -m json.tool
```

Expected: entity exists with state `off` or `on` (depending on amplifier power), source list showing Input 1–5 and AUX.

- [ ] **Step 4: Test power on/off**

```bash
# Turn on
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "media_player.logitech_z906"}' \
  "http://192.168.4.10:8123/api/services/media_player/turn_on"

# Verify amplifier turned on (check power sensor)
sleep 5
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://192.168.4.10:8123/api/states/sensor.amplifier_plug_power" | python3 -c "import json,sys;print(json.load(sys.stdin)['state'])"
```

Expected: power reading > 2W.

- [ ] **Step 5: Test source selection**

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "media_player.logitech_z906", "source": "Input 3"}' \
  "http://192.168.4.10:8123/api/services/media_player/select_source"
```

Expected: amplifier switches to input 3 (Chromecast SPDIF). Entity source attribute shows "Input 3".

- [ ] **Step 6: Test volume and mute**

```bash
# Volume up
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "media_player.logitech_z906"}' \
  "http://192.168.4.10:8123/api/services/media_player/volume_up"

# Mute
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "media_player.logitech_z906", "is_volume_muted": true}' \
  "http://192.168.4.10:8123/api/services/media_player/volume_mute"
```

Expected: volume changes audibly, mute toggles.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: complete Z906 integration — ready for deployment"
```

---

### Task 5: Remove old amplifier template switch

**Files:**
- Modify: `ha/ha-config/packages/amplifier.yaml` — keep power sensor, remove template switch
- Modify: `ha/ha-config/automations.yaml` — update amplifier automations to use new entity
- Modify: `ha/AUTOMATIONS.md` — update documentation

- [ ] **Step 1: Update amplifier automations to use media_player entity**

In `ha/ha-config/automations.yaml`, update the "Living Room - Amplifier - On" and "Living Room - Amplifier - Off" automations to use `media_player.logitech_z906` instead of `switch.amplifier`.

The on automation should also select the correct source based on what triggered it:
- Samsung TV / Google TV Streamer on → turn on + select Input 4
- (Future: Chromecast playing → turn on + select Input 3)

- [ ] **Step 2: Remove template switch from amplifier.yaml**

Remove the `switch.amplifier` template switch from `ha/ha-config/packages/amplifier.yaml`. Keep the power sensor configuration (it's used by the new component) and the `input_boolean.amplifier_assumed_state` (can be removed too since the component handles state internally).

- [ ] **Step 3: Deploy and verify automations still work**

Deploy updated automations.yaml and amplifier.yaml to HA, reload.

- [ ] **Step 4: Update AUTOMATIONS.md**

Update the amplifier automation entries to reference `media_player.logitech_z906`.

- [ ] **Step 5: Commit both repos**

```bash
# logitech-z906 repo
cd ha/logitech-z906
git add -A && git push

# ha repo
cd ..
git add ha-config AUTOMATIONS.md logitech-z906
git commit -m "feat: switch amplifier to Z906 component, remove template switch"
git push
```
