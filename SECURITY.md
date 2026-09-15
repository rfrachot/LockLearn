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
