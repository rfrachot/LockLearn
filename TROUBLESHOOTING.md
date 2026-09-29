# Troubleshooting

Start with Home Assistant logs, LockLearn Repairs and redacted diagnostics. Do not
delete `state.db` as a generic troubleshooting step.

## Notifications do not arrive

1. verify the Profile has an enabled resolved target;
2. check target capability/service resolution;
3. check Profile/Track/target quotas, quiet hours and minimum gap;
4. check scheduler/target Repairs;
5. verify Companion connectivity.

A missed delivery is operational state, not an SRS failure.

## Wrong/missing target

Renamed/removed devices can make a target unresolved. Use Repairs/target management
to reselect a device. LockLearn does not silently redirect private notifications to
a different device.

## Scheduler appears stopped

Check Profile timezone/windows/quiet hours, active Track demand, pending active
sessions and scheduler infeasibility Repairs. Restart/reload should reconcile
persisted high-watermark state rather than create catch-up floods.

## Database migration/integrity failure

Do not manually edit or downgrade the DB. LockLearn enters a safe/read-only recovery
path and surfaces a Repair. Use the documented snapshot recovery/backup options.

## Dataset/pack incompatible

Check dataset signature/schema/license/source validation and supported content schema
versions. Failed update/install must leave last-known-good content active. Tracks
remain pinned to their previous PackVersion until explicit integration.

## Panel missing/stale

- confirm the integration is loaded;
- hard reload the browser if frontend protocol/version changed;
- verify the full integration directory (not only JS bundle) was deployed;
- check the static panel path and browser console.

## Permission denied/not found

Profile membership role is authoritative. HA admin does not automatically bypass a
Profile ACL for private learner operations. Some global dataset/storage mutations do
require HA admin.

## Export/import failure

Private upload/download capabilities are short-lived and owner-bound. Reusing an
expired or another user's token fails closed.

## Diagnostics/support

Use Home Assistant diagnostics/Repairs where possible. Diagnostics are intentionally
redacted and should not contain profile names, learned content, answers or private
stats.
