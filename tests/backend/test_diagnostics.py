"""P6.3 redacted diagnostics tests."""

from __future__ import annotations

import json

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.locklearn.const import DATA_RUNTIME, DOMAIN
from custom_components.locklearn.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_are_aggregate_only_and_redact_private_values(
    hass: HomeAssistant,
) -> None:
    """Diagnostics never expose private values or Repair placeholders."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][DATA_RUNTIME]
    profile = await runtime.profiles.async_create_profile(
        name="PRIVATE_PROFILE_SENTINEL",
        preset="standard",
        timezone=hass.config.time_zone,
        owner_ha_user_ids=("private-user-id",),
    )
    await runtime.storage.async_create_session(
        "private-session-id",
        str(profile["profile_id"]),
        None,
        items=(
            {
                "question_id": "private-question-id",
                "card_key": "private-card-key",
                "learning_item_id": "PRIVATE_CONTENT_SENTINEL",
                "prompt_facet_id": "private-prompt",
                "answer_facet_id": "private-answer-facet",
                "payload": {},
            },
        ),
    )
    await runtime.storage.async_answer_session(
        "private-session-id",
        1,
        "private-question-id",
        {"text": "PRIVATE_RESPONSE_SENTINEL"},
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        "private-target-repair",
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="notification_target_unavailable",
        translation_placeholders={
            "target_id": "private-target-id",
            "friendly_name": "PRIVATE_PHONE_SENTINEL",
        },
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    rendered = json.dumps(diagnostics, sort_keys=True)

    assert diagnostics["versions"]["locklearn"]
    assert diagnostics["versions"]["home_assistant"]
    assert diagnostics["database"]["profile_count"] >= 1
    assert diagnostics["datasets"]["installed_dataset_count"] >= 1
    assert (
        diagnostics["errors"]["active_repair_types"][
            "notification_target_unresolved"
        ]
        == 1
    )
    assert "performance" in diagnostics
    assert diagnostics["performance"]["session.answer_ms"]["count"] >= 1

    for private_value in (
        "PRIVATE_PROFILE_SENTINEL",
        "PRIVATE_CONTENT_SENTINEL",
        "PRIVATE_RESPONSE_SENTINEL",
        "PRIVATE_PHONE_SENTINEL",
        "private-user-id",
        "private-target-id",
        "private-session-id",
        "private-card-key",
    ):
        assert private_value not in rendered

    await hass.config_entries.async_unload(entry.entry_id)
