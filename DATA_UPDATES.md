# Data update model

Official content follows the V1 pipeline:

```text
upstream source
→ CI adapter
→ normalized intermediate data
→ semantic + license validation
→ prebuilt SQLite dataset package
→ manifest + canonical content hash + Ed25519 signature
→ release artifact
→ LockLearn DatasetManager staging
→ local validation
→ merged content.next.db
→ atomic generation switch
```

Home Assistant does **not** parse the large raw upstream corpora during normal
updates. Runtime uses a single active generated `content.db` plus `state.db`.

A future `locklearn-data` repository should host adapters, scheduled builds and
official dataset release artifacts. Until that repository exists, this repo
contains only schemas, registries, tiny fixtures and validation tooling.
