from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, *, count: int | None = 1) -> None:
    p = Path(path)
    text = p.read_text()
    matches = text.count(old)
    if matches == 0:
        raise SystemExit(f"{path}: missing pattern {old!r}")
    if count is None:
        text = text.replace(old, new)
    else:
        if matches < count:
            raise SystemExit(f"{path}: expected >= {count}, found {matches}: {old!r}")
        text = text.replace(old, new, count)
    p.write_text(text)


# Unit tests must describe the new additive endpoints rather than pinning v0.3 names.
replace(
    "frontend/src/protocol.test.ts",
    '"locklearn/session/start"',
    '"locklearn/session/start_v04"',
    count=None,
)
replace(
    "frontend/src/protocol.test.ts",
    '"locklearn/session/answer"',
    '"locklearn/session/answer_v04"',
    count=None,
)
replace(
    "frontend/src/protocol.test.ts",
    '"locklearn/quiz/answer"',
    '"locklearn/quiz/answer_v04"',
    count=None,
)

# E2E HA harness serves both legacy and additive protocol names during the migration.
replace(
    "frontend/e2e/harness.ts",
    '      case "locklearn/session/start":\n        return session(message.session_type === "quiz" ? "quiz" : "learn");',
    '      case "locklearn/session/start":\n      case "locklearn/session/start_v04":\n        return session(message.session_type === "quiz" || message.session_type === "calibration" ? "quiz" : "learn");',
)
replace(
    "frontend/e2e/harness.ts",
    '      case "locklearn/session/answer":\n        return { ...session("learn"), version: 2 };',
    '      case "locklearn/session/answer":\n      case "locklearn/session/answer_v04":\n        return { ...session("learn"), version: 2 };',
)
replace(
    "frontend/e2e/harness.ts",
    '      case "locklearn/quiz/answer":\n        return {',
    '      case "locklearn/quiz/answer":\n      case "locklearn/quiz/answer_v04":\n        return {',
)
replace(
    "frontend/e2e/harness.ts",
    '      case "locklearn/reminders/ready/status":',
    '      case "locklearn/calibration/followup/status":\n        return { source_session_id: null, pending_count: 0, card_keys: [] };\n      case "locklearn/reminders/ready/status":',
)

# Update copy expectation to the user-facing v0.4 text.
replace(
    "frontend/e2e/tests/panel.spec.ts",
    '  await expect(page.getByText(/1 cards ready now/)).toBeVisible();',
    '  await expect(page.getByText(/1 cards ready for quiz/)).toBeVisible();',
)

print("beta5 polish CI fixtures updated")
