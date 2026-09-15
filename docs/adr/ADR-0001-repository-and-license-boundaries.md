# ADR-0001 — Repository and license boundaries

**Status:** Accepted for bootstrap

## Context

LockLearn software is intended for HACS/GitHub and may receive donations or
sponsorship. Official learning data will aggregate sources with different open
licenses, including ShareAlike obligations.

## Decision

- `locklearn` contains the Home Assistant integration, frontend, schemas,
  documentation, source manifests and small fixtures.
- software is MIT;
- original LockLearn learning/editorial content is intended to be CC BY-SA 4.0;
- third-party data/assets preserve upstream licenses;
- large official data builds/releases should move to a separate
  `locklearn-data` repository when the first pipeline is implemented.

## Alternatives considered

1. Put code and all datasets in one repository under MIT — rejected because it
   would blur or misstate upstream data licensing.
2. Make all code copyleft to match data — rejected; ShareAlike data does not
   require the application source code to use the same license.
3. Delay licensing until public release — rejected because license boundaries
   affect data architecture immediately.

## Consequences

Builds need explicit license/provenance metadata and may produce multiple
separately licensed artifacts. Donations remain compatible with the software
license, but do not change upstream obligations.
