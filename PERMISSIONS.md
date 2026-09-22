# Permissions

LockLearn authorization is profile-scoped and enforced by the backend.

## Identity model

```text
Profile != Home Assistant user
Profile != device
```

A Home Assistant user may be a member of zero, one, or many LockLearn
profiles. A profile may have multiple Home Assistant users as members, and a
child/shared profile does not need a dedicated Home Assistant account.

Membership is persisted in `profile_members(profile_id, ha_user_id, role)`.

## Roles

V1 roles are:

| Permission | owner | editor | viewer | outsider |
| --- | --- | --- | --- | --- |
| Read profile/progress/stats | yes | yes | yes | no |
| Edit profile metadata/settings | yes | no | no | no |
| Edit tracks/planning | yes | yes | no | no |
| Answer/start learning work | yes | yes | no | no |
| Manage progress | yes | yes | no | no |
| Share / manage ACL | yes | no | no | no |
| Delete profile | yes | no | no | no |

A profile always retains at least one owner.

## Home Assistant administrators

Home Assistant administrator status is deliberately not part of the normal
profile ACL decision. An HA admin is not automatically an owner, editor, or
viewer of every LockLearn profile.

Installation-level administrative operations such as storage diagnostics,
dataset management, migration, and Repairs may still require HA admin rights.
Those system privileges do not grant normal access to another learner's private
content.

## Privacy filtering

Normal profile listings are membership-filtered in SQL and return only profiles
the authenticated HA user may access. Direct visibility lookup returns the same
absence result for an unauthorized profile and a nonexistent profile.

Frontend checks are convenience only. Every profile-scoped backend operation
must call the centralized ACL authority before reading or mutating private
state.

## Home Assistant surfaces

Home Assistant entities and events are not equivalent to LockLearn ACL. Private
learning content must not be exposed through entities/events by default.
Profile/track sensors are opt-in and remain subject to the separate HA entity
permission model.
