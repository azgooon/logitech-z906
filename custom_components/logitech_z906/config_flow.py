"""Config flow for Logitech Z906."""

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers import selector

from .const import CONF_POWER_SENSOR, CONF_REMOTE_ENTITY, DOMAIN


class LogitechZ906ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Logitech Z906."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            if not user_input.get(CONF_POWER_SENSOR):
                user_input.pop(CONF_POWER_SENSOR, None)

            return self.async_create_entry(
                title="Logitech Z906",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REMOTE_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="remote")
                    ),
                    vol.Optional(CONF_POWER_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="power",
                        )
                    ),
                }
            ),
        )
