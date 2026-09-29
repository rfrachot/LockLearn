# AGENT_HANDOFF.md

## Current state

Release-preparation branch: `release/1.0.0-beta.1`.

P6.1 through P6.11 are PASS and the P6 exit gate is PASS. The final qualified
feature baseline is:

```text
3f980a4fba936c2d8124a47dec4e61e3554f5a2f
```

Independent P6.11 qualification reported 487 Python tests PASS, 49 Vitest tests,
3 Playwright tests and no V1 blocker. GitHub Actions run `36542238235` passed
backend, datasets, frontend/E2E, HA minimum 2025.2.5, current harness 2026.9.3,
latest-stable smoke 2026.9.4, HACS and hassfest on that exact SHA.

Stable `v1.0.0` has deliberately **not** been published. The next phase is
real Home Assistant field validation using `1.0.0-beta.1`.

## Beta preparation

The beta branch changes release metadata/contracts only:

- runtime/manifest version: `1.0.0-beta.1`;
- SemVer release gates accept an explicit prerelease suffix while retaining one
  authoritative runtime version;
- P6.11/P6 exit status is recorded as PASS;
- `CHANGELOG.md` contains the dated beta section;
- `RELEASE.md` defines immutable beta tags and the field-validation gate;
- `docs/BETA_VALIDATION.md` is the real-HA beta checklist.

Do not add features during beta deployment. A discovered runtime defect gets a
new beta commit/tag (`beta.2`, etc.) after review.

## Beta publication/deployment boundary

Before deployment:

1. require complete CI success on the exact beta commit;
2. create `v1.0.0-beta.1` from that exact commit;
3. publish a GitHub Release marked **Pre-release**;
4. do not publish stable `v1.0.0`;
5. use the dedicated HA test instance and make a backup before installation.

The field-validation procedure is a release-readiness gate;
`SPEC_V1.md` remains the product/architecture source of truth.
