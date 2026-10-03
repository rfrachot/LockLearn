"""Beta.5 grading polish regression tests."""

from custom_components.locklearn.core.content import GradingOutcome, GradingPolicyKind
from custom_components.locklearn.core.grading import FreeTextGrader
from custom_components.locklearn.core.localization import (
    CaseMode,
    NormalizationPolicy,
    PunctuationMode,
    UnicodeNormalization,
    WhitespaceMode,
)


def _quiz_policy(script: str) -> NormalizationPolicy:
    return NormalizationPolicy(
        policy_id="quiz_free_text",
        normalization_version=1,
        unicode_normalization=UnicodeNormalization.NFC,
        case_mode=CaseMode.PRESERVE,
        whitespace_mode=WhitespaceMode.COLLAPSE,
        punctuation_mode=PunctuationMode.PRESERVE,
        allowed_scripts=(script,),
    )


def test_exact_romaji_is_case_insensitive_without_becoming_fuzzy() -> None:
    grader = FreeTextGrader()
    for submitted in ("ko", "Ko", "KO"):
        result = grader.grade(
            submitted,
            accepted_answers=("ko",),
            grading_policy_kind=GradingPolicyKind.EXACT,
            grading_policy_version=1,
            normalization_policy=_quiz_policy("Latn"),
            script="Latn",
        )
        assert result.outcome is GradingOutcome.CORRECT
        assert result.normalized_submission == "ko"

    wrong = grader.grade(
        "ka",
        accepted_answers=("ko",),
        grading_policy_kind=GradingPolicyKind.EXACT,
        grading_policy_version=1,
        normalization_policy=_quiz_policy("Latn"),
        script="Latn",
    )
    assert wrong.outcome is GradingOutcome.WRONG


def test_quiz_casefold_is_not_applied_to_non_latin_scripts() -> None:
    grader = FreeTextGrader()
    result = grader.grade(
        "カナ",
        accepted_answers=("かな",),
        grading_policy_kind=GradingPolicyKind.EXACT,
        grading_policy_version=1,
        normalization_policy=_quiz_policy("Kana"),
        script="Kana",
    )
    assert result.outcome is GradingOutcome.WRONG


def test_any_of_latin_uses_same_casefolded_membership_without_typo_tolerance() -> None:
    grader = FreeTextGrader()
    correct = grader.grade(
        "REST",
        accepted_answers=("rest", "take a rest"),
        grading_policy_kind=GradingPolicyKind.ANY_OF,
        grading_policy_version=1,
        normalization_policy=_quiz_policy("Latn"),
        script="Latn",
    )
    wrong = grader.grade(
        "rests",
        accepted_answers=("rest", "take a rest"),
        grading_policy_kind=GradingPolicyKind.ANY_OF,
        grading_policy_version=1,
        normalization_policy=_quiz_policy("Latn"),
        script="Latn",
    )
    assert correct.outcome is GradingOutcome.CORRECT
    assert correct.matched_answer == "rest"
    assert wrong.outcome is GradingOutcome.WRONG
