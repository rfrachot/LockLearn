# Security

LockLearn treats frontend input, imported archives and third-party dataset
content as untrusted.

Core invariants:
- backend ACL on every profile-scoped operation;
- parameterized SQL only;
- no blocking DB I/O on the HA event loop;
- no raw third-party HTML or `unsafeHTML`;
- sanitize SVG and reject external references/scripts;
- reject archive traversal, links and archive bombs;
- verify official dataset signatures before activation;
- keep private learning content out of HA events/entities by default;
- redact personal content from diagnostics.

A public vulnerability reporting channel will be added before the repository is
made public.


## Profile ACL authority

Profile authorization is centralized in the backend. The role matrix is
owner/editor/viewer and is evaluated from persistent `profile_members`.
Home Assistant administrator status is intentionally not a profile-ownership
shortcut.

Unauthorized profiles are removed from normal listings rather than returned as
discoverable forbidden rows. Direct visibility checks collapse nonexistent and
unauthorized profiles to the same absence result.

ACL changes are owner-only and cannot remove or demote the final owner of a
profile. Frontend permission checks never replace this backend authority.

See `PERMISSIONS.md` and `PRIVACY.md` for the user-facing contract.
