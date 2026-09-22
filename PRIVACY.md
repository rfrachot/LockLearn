# Privacy

LockLearn is local-first and multi-user. User learning state is private by
default even when several people share the same Home Assistant instance.

## Private data

Private profile state includes, among other things:

- profile identity and membership;
- tracks and learning configuration;
- progress, review history, answers and sessions;
- statistics, annotations and mnemonics;
- notification targets and interaction history.

Normal backend listings omit profiles entirely for users who are not members.
They are not returned as visible-but-forbidden rows.

## Shared data

A profile is shared only through explicit `profile_members` membership.
Owners may manage sharing; editors and viewers receive only the permissions
defined in `PERMISSIONS.md`.

A child/shared profile may have several owners and no dedicated HA account.

## Home Assistant administrators

HA administrator status does not automatically expose another learner's profile
inside normal LockLearn APIs. System-level diagnostics and maintenance remain a
separate administrative boundary and should expose aggregate/redacted metadata
only.

## Home Assistant entities and events

LockLearn ACL and Home Assistant entity permissions are separate systems.
Detailed learning data belongs in the authenticated LockLearn panel.

Sensors are opt-in per profile/track and must not expose studied vocabulary,
answers, annotations, or other personal learning content by default. Home
Assistant events likewise carry only the minimum data required for automation.

## Companion App notifications

Notification payloads necessarily leave Home Assistant for the selected
Companion target. Lock-screen visibility is advisory OS behavior, not a
confidentiality boundary. Shared-device targets are treated as lower-confidence
learning signals unless explicitly trusted.

## Export and backup

`state.db` contains persistent private learning state and is included in
coherent backups. Reconstructible public content caches are separate.

Secure export/import is a later V1 hardening work package. Until that boundary
is implemented, no API should expose bulk private profile state by default.
