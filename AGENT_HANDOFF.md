# AGENT_HANDOFF.md

## Current state

Release-fix branch: `release/1.0.0-beta.2`.

P6.1 through P6.11 and the P6 exit gate remain PASS on the qualified feature
baseline `3f980a4fba936c2d8124a47dec4e61e3554f5a2f`.

`v1.0.0-beta.1` is published and immutable. Real Home Assistant field
validation proved HACS installation, Config Flow, panel, starter, Learn/Quiz,
dashboard/stats, FR/EN, reload/restart, persistence and backups, but returned:

```text
BETA FIELD VALIDATION BLOCKED
```

The blocker was not notification delivery itself: no LockLearn notification
target could be created through any public/user-facing path.

## Beta.2 fix

Beta.2 closes only that V1 configuration gap:

- owner-only `locklearn/targets/discover` enumerates real enabled Companion
  `mobile_app` Device Registry candidates;
- owner-only `locklearn/targets/create` persists stable
  `device_registry_id` identity without optimistic capability assumptions;
- owner-only `locklearn/targets/update` edits target privacy/share/budget
  settings without changing stable identity;
- existing `locklearn/targets/list` remains usable by Track editors and now
  returns the complete authorized target configuration needed by Settings;
- Settings exposes Companion target add/edit controls;
- target capabilities remain evidence-driven; unknown is never upgraded to
  supported from platform name alone;
- Pack inventory exposes valid prompt-language → answer-language directions,
  and Track creation uses those directions instead of free-form language codes;
- WebSocket object errors are rendered as their actionable message instead of
  `[object Object]`;
- P6.8 command classification/negative ACL and dedicated target-management
  regressions cover the new path.

No state schema migration and no new pedagogical feature are part of beta.2.

## Next gate

Run the complete release CI on the exact beta.2 commit. Only if green:

1. tag immutable `v1.0.0-beta.2`;
2. publish GitHub Release as **Pre-release**;
3. upgrade the existing HA test VM from beta.1 through HACS;
4. configure a real Companion target through LockLearn;
5. qualify Learning + Quiz notifications and available fallback/Repair paths;
6. do not create stable `v1.0.0` and do not merge PR #3 until explicit
   field-validation acceptance.
