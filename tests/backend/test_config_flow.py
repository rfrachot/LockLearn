"""Config-flow contract tests."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.locklearn.const import DOMAIN


async def test_user_flow_creates_single_entry(hass: HomeAssistant) -> None:
    """The UI flow creates one entry without YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"create_personal_profile": True, "ui_language": "fr"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"create_personal_profile": True, "ui_language": "fr"}

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "single_instance_allowed"
