"""Config flow for LockLearn."""

from typing import Any, override

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_CREATE_PERSONAL_PROFILE,
    CONF_UI_LANGUAGE,
    DEFAULT_UI_LANGUAGE,
    DOMAIN,
    SUPPORTED_UI_LANGUAGES,
)


class LockLearnConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the LockLearn config flow."""

    VERSION = 1

    @override
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Create the single LockLearn config entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="LockLearn", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_CREATE_PERSONAL_PROFILE, default=True): bool,
                vol.Optional(CONF_UI_LANGUAGE, default=DEFAULT_UI_LANGUAGE): vol.In(
                    SUPPORTED_UI_LANGUAGES
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
