"""Power sensor for Logitech Z906 (mirrors configured power entity)."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_POWER_SENSOR, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up power sensor if configured."""
    conf = hass.data[DOMAIN][entry.entry_id]
    if conf.get(CONF_POWER_SENSOR):
        async_add_entities([Z906PowerSensor(hass, conf)])


class Z906PowerSensor(SensorEntity):
    """Power consumption sensor for the Z906."""

    _attr_has_entity_name = True
    _attr_name = "Power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self._source_entity = config[CONF_POWER_SENSOR]
        self._attr_unique_id = "logitech_z906_power"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "logitech_z906")},
        }

    async def async_added_to_hass(self) -> None:
        """Start tracking the source power sensor."""
        self._update_from_source()
        async_track_state_change_event(
            self.hass, [self._source_entity], self._source_changed
        )

    @callback
    def _source_changed(self, event) -> None:
        self._update_from_source()
        self.async_write_ha_state()

    @callback
    def _update_from_source(self) -> None:
        state = self.hass.states.get(self._source_entity)
        if state is None or state.state in ("unavailable", "unknown"):
            self._attr_native_value = None
            return
        try:
            self._attr_native_value = round(float(state.state), 1)
        except (ValueError, TypeError):
            self._attr_native_value = None
