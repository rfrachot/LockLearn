"""P1.4 multilingual normalization and locale primitive tests."""

from dataclasses import replace

import pytest

from custom_components.locklearn.core import content as m
from custom_components.locklearn.core import localization as loc


def _latin_policy(*, version: int = 1) -> loc.NormalizationPolicy:
    return loc.NormalizationPolicy(
        policy_id="latin_default_v1",
        normalization_version=version,
        unicode_normalization=loc.UnicodeNormalization.NFC,
        case_mode=loc.CaseMode.CASEFOLD,
        whitespace_mode=loc.WhitespaceMode.COLLAPSE,
        punctuation_mode=loc.PunctuationMode.PRESERVE,
        allowed_scripts=("Latn",),
    )


def test_bcp47_tags_are_canonicalized_without_losing_specificity() -> None:
    assert loc.canonicalize_language_tag("fr-fr") == "fr-FR"
    assert loc.canonicalize_language_tag("zh-hant-tw") == "zh-Hant-TW"
    assert loc.canonicalize_language_tag("de-DE-u-co-phonebk") == "de-DE-u-co-phonebk"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "fr_FR",
        "f",
        "fr-",
        "fr-Latnn",
        "en-US-u",
        "de-1901-1901",
    ],
)
def test_invalid_bcp47_tags_fail_closed(value: str) -> None:
    with pytest.raises(loc.LocalizationError):
        loc.parse_language_tag(value)


def test_iso15924_script_codes_use_canonical_casing() -> None:
    assert loc.canonicalize_script_code("latn") == "Latn"
    assert loc.canonicalize_script_code("JPAN") == "Jpan"

    with pytest.raises(loc.LocalizationError):
        loc.canonicalize_script_code("Latin")


def test_locale_fallback_is_exact_then_base_then_explicit_default() -> None:
    assert loc.language_fallback_chain(
        "fr-FR",
        default_tag="en-GB",
        final_fallback_tag="en",
    ) == ("fr-FR", "fr", "en-GB", "en")

    assert (
        loc.resolve_localized_value(
            {"fr": "Bonjour", "en": "Hello"},
            "fr-CA",
            default_tag="en",
        )
        == "Bonjour"
    )


def test_locale_fallback_never_invents_missing_translation() -> None:
    assert (
        loc.resolve_localized_value(
            {"de": "Hallo"},
            "fr-FR",
            default_tag="en",
        )
        is None
    )


def test_canonicalized_locale_keys_cannot_collide() -> None:
    with pytest.raises(loc.LocalizationError, match="canonicalize"):
        loc.resolve_localized_value(
            {"fr-fr": "A", "fr-FR": "B"},
            "fr-FR",
        )


def test_latin_policy_casefolds_and_collapses_space_but_preserves_accents() -> None:
    policy = _latin_policy()
    assert loc.normalize_text("  AÑO   Été  ", policy, script="latn") == "año été"
    assert loc.normalize_text("ano", policy, script="Latn") != loc.normalize_text(
        "año",
        policy,
        script="Latn",
    )


def test_nfkc_policy_can_normalize_width_without_language_branching() -> None:
    policy = loc.NormalizationPolicy(
        policy_id="japanese_v1",
        normalization_version=1,
        unicode_normalization=loc.UnicodeNormalization.NFKC,
        whitespace_mode=loc.WhitespaceMode.COLLAPSE,
        allowed_scripts=("Jpan", "Kana"),
    )
    assert loc.normalize_text("ｶﾀｶﾅ", policy, script="Kana") == "カタカナ"


def test_policy_rejects_scripts_not_declared_by_data() -> None:
    with pytest.raises(loc.LocalizationError, match="not allowed"):
        loc.normalize_text("hello", _latin_policy(), script="Hira")


def test_punctuation_policy_is_generic_and_explicit() -> None:
    policy = loc.NormalizationPolicy(
        policy_id="free_text_v1",
        normalization_version=1,
        punctuation_mode=loc.PunctuationMode.REMOVE,
        whitespace_mode=loc.WhitespaceMode.COLLAPSE,
    )
    assert loc.normalize_text("hello,   world!", policy) == "hello world"


def test_behavior_change_requires_normalization_version_bump() -> None:
    previous = _latin_policy(version=1)
    changed_same_version = replace(
        previous,
        punctuation_mode=loc.PunctuationMode.REMOVE,
    )
    with pytest.raises(loc.LocalizationError, match="higher normalization_version"):
        loc.normalization_rebuild_required(previous, changed_same_version)

    changed_v2 = replace(
        changed_same_version,
        normalization_version=2,
    )
    assert loc.normalization_rebuild_required(previous, changed_v2) is True
    assert loc.normalization_rebuild_required(previous, previous) is False


def test_normalization_version_cannot_move_backwards() -> None:
    previous = _latin_policy(version=2)
    current = _latin_policy(version=1)
    with pytest.raises(loc.LocalizationError, match="cannot move backwards"):
        loc.normalization_rebuild_required(previous, current)


def test_term_language_script_and_normalization_metadata_are_canonical() -> None:
    term = m.Term(
        "locklearn:term:summer",
        "locklearn:dataset:starter",
        "fr-fr",
        "Été",
        "latn",
    )
    assert term.language_tag == "fr-FR"
    assert term.script == "Latn"
    assert term.normalized_text is None
    assert term.normalization_version is None

    normalized = term.with_normalization(_latin_policy())
    assert normalized.term_id == term.term_id
    assert normalized.text == term.text
    assert normalized.normalized_text == "été"
    assert normalized.normalization_version == 1


def test_term_normalization_metadata_is_pairwise_and_non_identifying() -> None:
    with pytest.raises(m.ContentModelError, match="set together"):
        m.Term(
            "locklearn:term:bad",
            "locklearn:dataset:starter",
            "en",
            "Hello",
            "Latn",
            normalized_text="hello",
        )

    before = m.Term(
        "locklearn:term:hello",
        "locklearn:dataset:starter",
        "en",
        "Hello",
        "Latn",
    )
    after = before.with_normalization(_latin_policy())
    assert before.term_id == after.term_id


def test_core_has_no_language_specific_normalization_switch() -> None:
    policy = loc.NormalizationPolicy(
        policy_id="custom_script_v1",
        normalization_version=1,
        unicode_normalization=loc.UnicodeNormalization.NFC,
        case_mode=loc.CaseMode.PRESERVE,
        whitespace_mode=loc.WhitespaceMode.PRESERVE,
        allowed_scripts=("Cyrl",),
    )
    assert loc.normalize_text("Тест", policy, script="Cyrl") == "Тест"
