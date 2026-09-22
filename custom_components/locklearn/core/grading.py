"""Panel free-text grading and recoverable content-quality feedback."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace

from .content import GradingOutcome, GradingPolicyKind
from .localization import NormalizationPolicy, normalize_text


class GradingError(ValueError):
    """Raised when free-text grading metadata or input is invalid."""


@dataclass(frozen=True, slots=True)
class FreeTextGradingResult:
    """Versioned grading result suitable for ReviewEvent persistence."""

    outcome: GradingOutcome
    submitted_text: str
    normalized_submission: str | None
    matched_answer: str | None
    grading_policy_kind: GradingPolicyKind
    grading_policy_version: int
    normalization_version: int
    reportable: bool = False
    reason: str = ""

    @property
    def is_definitive_failure(self) -> bool:
        """Return whether SRS may safely treat this result as wrong."""
        return self.outcome.is_definitive_failure


class FreeTextGrader:
    """Execute exact, any-of and conservative fuzzy-normalized policies."""

    def grade(
        self,
        submitted_text: str,
        *,
        accepted_answers: tuple[str, ...],
        grading_policy_kind: GradingPolicyKind | str,
        grading_policy_version: int,
        normalization_policy: NormalizationPolicy,
        script: str | None = None,
    ) -> FreeTextGradingResult:
        """Grade one panel free-text response with explicit version metadata."""
        if grading_policy_version < 1:
            raise GradingError("grading_policy_version must be >= 1")
        if not accepted_answers or any(answer == "" for answer in accepted_answers):
            raise GradingError("accepted_answers must contain non-empty values")

        kind = GradingPolicyKind(grading_policy_kind)
        if kind is GradingPolicyKind.RULE_BASED_RESERVED:
            raise GradingError("rule_based_reserved is not implemented in V1")

        if kind is GradingPolicyKind.EXACT:
            if len(accepted_answers) != 1:
                raise GradingError("exact grading requires exactly one accepted answer")
            matched = accepted_answers[0] if submitted_text == accepted_answers[0] else None
            return FreeTextGradingResult(
                outcome=GradingOutcome.CORRECT if matched is not None else GradingOutcome.WRONG,
                submitted_text=submitted_text,
                normalized_submission=None,
                matched_answer=matched,
                grading_policy_kind=kind,
                grading_policy_version=grading_policy_version,
                normalization_version=normalization_policy.normalization_version,
                reason="exact_match" if matched is not None else "exact_mismatch",
            )

        if kind is GradingPolicyKind.ANY_OF:
            matched = next((answer for answer in accepted_answers if submitted_text == answer), None)
            return FreeTextGradingResult(
                outcome=GradingOutcome.CORRECT if matched is not None else GradingOutcome.WRONG,
                submitted_text=submitted_text,
                normalized_submission=None,
                matched_answer=matched,
                grading_policy_kind=kind,
                grading_policy_version=grading_policy_version,
                normalization_version=normalization_policy.normalization_version,
                reason="any_of_match" if matched is not None else "any_of_mismatch",
            )

        if not normalization_policy.allowed_scripts:
            raise GradingError(
                "fuzzy_normalized requires an explicit supported-script normalization policy"
            )
        normalized_submission = normalize_text(
            submitted_text,
            normalization_policy,
            script=script,
        )
        normalized_answers = tuple(
            (
                answer,
                normalize_text(
                    answer,
                    normalization_policy,
                    script=script,
                ),
            )
            for answer in accepted_answers
        )
        exact_normalized = next(
            (answer for answer, normalized in normalized_answers if normalized == normalized_submission),
            None,
        )
        if exact_normalized is not None:
            return FreeTextGradingResult(
                outcome=GradingOutcome.CORRECT,
                submitted_text=submitted_text,
                normalized_submission=normalized_submission,
                matched_answer=exact_normalized,
                grading_policy_kind=kind,
                grading_policy_version=grading_policy_version,
                normalization_version=normalization_policy.normalization_version,
                reason="normalized_match",
            )

        fuzzy_match = self._single_edit_match(normalized_submission, normalized_answers)
        return FreeTextGradingResult(
            outcome=GradingOutcome.CORRECT if fuzzy_match is not None else GradingOutcome.WRONG,
            submitted_text=submitted_text,
            normalized_submission=normalized_submission,
            matched_answer=fuzzy_match,
            grading_policy_kind=kind,
            grading_policy_version=grading_policy_version,
            normalization_version=normalization_policy.normalization_version,
            reason="fuzzy_single_edit_match" if fuzzy_match is not None else "fuzzy_mismatch",
        )

    @staticmethod
    def mark_should_be_accepted(result: FreeTextGradingResult) -> FreeTextGradingResult:
        """Convert a disputed non-correct grade into recoverable unrecognized evidence."""
        if result.outcome is GradingOutcome.CORRECT:
            raise GradingError("a correct answer cannot be marked unrecognized")
        return replace(
            result,
            outcome=GradingOutcome.UNRECOGNIZED,
            reportable=True,
            reason="user_claimed_should_be_accepted",
        )

    @classmethod
    def _single_edit_match(
        cls,
        submitted: str,
        accepted: tuple[tuple[str, str], ...],
    ) -> str | None:
        if len(submitted) < 4:
            return None
        for original, normalized in accepted:
            if len(normalized) < 4:
                continue
            if cls._diacritic_only_difference(submitted, normalized):
                continue
            if cls._edit_distance_at_most_one(submitted, normalized):
                return original
        return None

    @staticmethod
    def _diacritic_only_difference(left: str, right: str) -> bool:
        """Keep semantically preserved accents from being accepted as fuzzy typos."""

        def strip_marks(value: str) -> str:
            decomposed = unicodedata.normalize("NFD", value)
            return "".join(
                character
                for character in decomposed
                if unicodedata.category(character) != "Mn"
            )

        return left != right and strip_marks(left) == strip_marks(right)

    @staticmethod
    def _edit_distance_at_most_one(left: str, right: str) -> bool:
        """Return whether two strings differ by at most one edit."""
        if abs(len(left) - len(right)) > 1:
            return False
        if left == right:
            return True
        if len(left) > len(right):
            left, right = right, left

        if len(left) == len(right):
            mismatches = sum(a != b for a, b in zip(left, right, strict=True))
            return mismatches <= 1

        left_index = 0
        right_index = 0
        edits = 0
        while left_index < len(left) and right_index < len(right):
            if left[left_index] == right[right_index]:
                left_index += 1
                right_index += 1
                continue
            edits += 1
            if edits > 1:
                return False
            right_index += 1
        return True
