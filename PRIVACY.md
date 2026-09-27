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

LockLearn 1.0 does not ship optional private learning `SensorEntity` entities;
the existing dataset `UpdateEntity` platform exposes public dataset/update
metadata only.

Any future learning sensor must obey `ha_entity_contract.py`:

- exposure requires explicit Profile **and** Track opt-in;
- every metric is disabled by default;
- entity identity derives from the stable Track UUID, never display names;
- sensors for a Profile share one logical Profile Device;
- default state attributes are empty and never contain studied content, answers,
  annotations, target/device details or Profile/Track names;
- publish cadence is debounced to at least five minutes;
- Recorder exclusion is recommended for noisy counters/snapshots;
- `state_class` is used only when the HA long-term-statistics semantics are
  genuinely valid.

The LockLearn panel remains the recommended surface for detailed/private
statistics. Home Assistant events likewise carry only the minimum data required
for automation and do not include words/translations/responses in clear text by
default.

## Companion App notifications

Notification payloads necessarily leave Home Assistant for the selected
Companion target. Lock-screen visibility is advisory OS behavior, not a
confidentiality boundary. Shared-device targets are treated as lower-confidence
learning signals unless explicitly trusted.

## Export and backup

`state.db` contains persistent private learning state and is included in
coherent backups. Reconstructible public content caches are separate.

Profile export/import is implemented through authenticated, owner-bound private
temporary transfers. Export URLs are short-lived and one-shot; imported
archives are validated and applied to a new archived Profile rather than
overwriting existing learner state. Private exports are never public static
assets.
