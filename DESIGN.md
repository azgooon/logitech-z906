# Logitech Z906 Custom Component — Design Spec

## Goal

A custom Home Assistant integration that exposes the Logitech Z906 5.1 speaker system as a `media_player` entity, controlled via IR through an existing Broadlink RM Pro. Provides power, volume, mute, source selection, and effects — all the commands the Z906 remote supports.

## Entity

`media_player.logitech_z906`

## Capabilities

| Feature | Method | State tracking |
|---------|--------|---------------|
| Power on/off | IR via Broadlink | Real — power sensor (>2W = on) |
| Volume up/down | IR via Broadlink | Not tracked (one-way IR) |
| Mute | IR via Broadlink | Assumed toggle |
| Source select | IR via Broadlink (discrete codes per input) | Assumed — tracks last command sent |
| Effect | IR via Broadlink | Assumed toggle |
| Level | IR via Broadlink | Not tracked |

## Source List

| Source name | Broadlink command | Use case |
|-------------|-------------------|----------|
| Input 1 | input1 | — |
| Input 2 | input2 | — |
| Input 3 | input3 | Chromecast Audio (SPDIF) |
| Input 4 | input4 | TV (SPDIF) |
| Input 5 | input5 | — |
| AUX | aux | — |

## IR Delivery

The component does NOT store IR codes. It calls `remote.send_command` on the configured Broadlink entity, referencing the device name and command stored in Broadlink's own storage file (`/config/.storage/broadlink_remote_*_codes`).

Example call:
```python
await hass.services.async_call("remote", "send_command", {
    "entity_id": "remote.broadlink_rm_pro_remote",
    "device": "Logitech",
    "command": "input3",
})
```

## Existing Broadlink Commands

Already stored in `/config/.storage/broadlink_remote_34ea34b526ab_codes` under device "Logitech":

- `on`, `off` — power
- `volumeUp`, `volumeDown` — volume
- `mute` — mute toggle
- `input1` through `input5`, `aux` — discrete source selection
- `effect` — effect cycle
- `level` — volume level mode
- `nextChannel` — input cycle (not used, discrete codes preferred)

## State Tracking

### Power
Real feedback from `sensor.amplifier_plug_power`:
- Reading > threshold (2W) = on
- Reading < threshold = off
- Polls every time HA updates the sensor (already ~2s via ESPHome)

### Source
Assumed state stored internally with restore state:
- Updated when the component sends a source command
- Persists across HA restarts
- No way to verify — if someone uses the physical remote, state drifts

### Mute
Assumed toggle — tracked internally, no verification possible.

### Volume
Not tracked. Volume up/down are fire-and-forget IR commands. The media player card will show volume buttons but no slider/level indicator.

## Configuration

```yaml
# configuration.yaml
logitech_z906:
  remote_entity: remote.broadlink_rm_pro_remote
  remote_device: Logitech
  power_sensor: sensor.amplifier_plug_power
  power_threshold: 2
```

## File Structure

```
custom_components/logitech_z906/
  __init__.py          # Integration setup
  manifest.json        # Integration metadata
  media_player.py      # Media player entity
  const.py             # Constants (commands, sources)
```

## Media Player Platform Features

```python
SUPPORT_FLAGS = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
)
```

## Dashboard

Standard `media-control` card — shows:
- Power button
- Source dropdown (Input 1–5, AUX)
- Volume up/down buttons
- Mute button

No custom card needed.

## Constraints

- One-way IR only — no state feedback except power sensor
- If physical remote is used, assumed state drifts until next command from HA
- Volume has no absolute level — only relative up/down
- The component depends on the Broadlink integration being configured with the Z906 IR codes already learned
