# LockLearn 1.0.0-beta.2 — Home Assistant field validation

This checklist validates the already-qualified V1 package on a real Home
Assistant test instance before stable `1.0.0`. It is not a new feature phase.

`1.0.0-beta.1` passed installation, sessions, persistence and UI validation
but was field-blocked because no public/user-facing path existed to configure a
notification target. Beta.2 closes that gap and must re-run the notification
portion of field validation.

## Preconditions

- exact GitHub prerelease: `v1.0.0-beta.2`;
- GitHub Release is marked **Pre-release**;
- release CI is green on the tag target;
- Home Assistant test instance is on a supported version;
- HACS is working;
- full HA backup/snapshot exists before installation;
- Companion targets used for notification tests are available.

Record HA Core/Supervisor/OS/frontend versions and the beta commit SHA.

## Installation path

1. Add `https://github.com/rfrachot/LockLearn` as a HACS custom Integration
   repository if it is not already configured.
2. Enable/select prerelease versions for LockLearn in HACS.
3. Install exactly `1.0.0-beta.2`.
4. Restart Home Assistant when requested.
5. Add LockLearn through Settings → Devices & services.
6. Confirm the sidebar panel loads and reports backend/runtime
   `1.0.0-beta.2`.

Do not copy development files over the HACS install.

## Fresh-instance acceptance

Verify on the real instance:

- Config Flow completes once and remains single-instance;
- bundled Japanese Starter is available offline;
- create a Profile and Track;
- start Learn and Quiz sessions;
- fresh 20-card request respects the §53.1 final-quarter reserve;
- session survives panel navigation and resumes correctly;
- dashboard/stats load without private-data leakage;
- Sources & Licences shows provenance/licensing;
- FR/EN interface switching works;
- reload of the integration does not duplicate panel/scheduler/resources;
- Home Assistant restart preserves Profile/Track/session state.

## Companion notification acceptance

Using real configured Companion targets:

- learning notification is delivered;
- reveal/exposure behavior is correct for the device capability;
- supported actions are recorded exactly once;
- quiz action path records one result only;
- shared-device notification visibly identifies the Profile;
- replay/duplicate action does not double-apply;
- renamed/unavailable target surfaces the expected Repair and recovers after
  target repair.

Do not use notification delivery latency as retrieval/SRS evidence.

## Backup/recovery acceptance

- create a Home Assistant backup with LockLearn state present;
- verify LockLearn unload/reload around backup is clean;
- restore in the test environment or an isolated clone when practical;
- confirm Profile/Track/progress/session state is coherent after restore;
- confirm no downgrade of migrated state is attempted.

## Dataset/update acceptance

- inspect installed dataset/version/provenance;
- exercise refresh/update path when an update candidate is available;
- verify explicit PackVersion integration semantics;
- verify an invalid/signature-invalid candidate preserves last-known-good
  content and raises the expected Repair;
- confirm learning progress is not silently lost.

## Observation window

Use the beta as a real test installation, not only a five-minute smoke. Record:

- crashes/exceptions/Repairs;
- frontend/backend protocol mismatch;
- scheduler duplication or missed/catch-up floods;
- notification action anomalies;
- persistence/restart issues;
- backup/restore issues;
- dataset/update problems;
- obvious UX blockers for normal V1 use.

A cosmetic improvement or deferred V1.1 feature is not by itself a beta blocker.

## Exit

Beta field validation is PASS only when:

- exact prerelease install through HACS works;
- core real-instance scenarios above pass;
- no unresolved V1 blocker remains;
- any discovered beta defect has either been fixed in a newer beta or explicitly
  classified non-blocking under the V1 spec.

After explicit acceptance, prepare stable `1.0.0` from the accepted beta line,
rerun the complete release matrix, tag `v1.0.0`, publish the stable GitHub
Release and verify HACS stable discovery.
