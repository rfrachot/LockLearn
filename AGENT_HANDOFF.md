# AGENT_HANDOFF.md

## Mission F04 — audit et correction consolidés (2026-10-11)

- Branche : `docs/f04-event-outbox-contract`, PR #16 vers
  `chore/self-hosted-ci`; aucun merge/tag/release effectué.
- Corrections : reprise déterministe au point temporel du `ReviewEvent`,
  capture durable des métadonnées/réglages de livraison, contexte de trigger
  reconstructible, rollback strict si l’intention outbox manque, et tests des
  frontières commit/payload/émission/acquittement/concurrence/migration.
- Validations locales de cette passe : Ruff format/check, mypy (189 fichiers),
  ressources, schémas, contrats docs, release smoke, 561 pytest, frontend
  lint/typecheck, 69 Vitest, no-polling, build, bundle, 10 Playwright E2E et
  capture de documentation — toutes vertes. Les deux scénarios de récupération
  à 205 événements passent, avec et sans contexte initial invalide. Un
  avertissement ZIP du test de profil hostile reste attendu.
- Garantie réelle : persistance atomique de l’intention avec le résultat
  pédagogique et reprise at-least-once ; exactement une fois impossible à
  garantir entre publication HA et acquittement SQLite. Les consommateurs
  doivent dédupliquer par `event_id` + type d’événement.
- Résidu connu : `npm audit` signale une vulnérabilité haute de développement
  dans `source-map-js@1.2.1` via Vite/PostCSS; `npm audit --omit=dev` est propre.
- Prochaine action : créer le commit consolidé, pousser la branche de la PR et
  suivre les huit jobs CI sur le SHA final. Ne pas fusionner.

## Mission and branch

Beta.5 final qualification, tests and deployment on
`feat/beta5-final-polish-v05`. No merge, tag or release was created.

## Verified state

- Qualification HEAD before this handoff update: `35c024b845406374338a14eb71e117bc94c60cb9`.
- Commits: `7d21cebe` synchronized the generated frontend bundle;
  `35c024b8` refreshed the generated documentation screenshot.
- CI run `37167605598` is green on the exact HEAD: frontend, frontend E2E and
  screenshot, backend quality, dataset contracts, HA minimum 2025.2.5, current
  harness 2026.9.3, latest stable smoke 2026.9.4 and hassfest/HACS.
- Local gates: Ruff format/check, mypy, resource/schema/docs contracts, 529
  pytest tests, frontend lint/typecheck, 69 Vitest tests, no-polling, build,
  bundle check and 10 Playwright E2E. The expected duplicate ZIP warning remains.
- `npx playwright install --with-deps chromium` cannot install system packages
  locally because sudo requires interactive authentication; CI installed it and
  passed the full E2E job.

## Real HA deployment

- HA test: 2026.7.4. Pre-deploy backup: `PRE_BETA5_BUNDLE_35C024B8`, backup
  slug `da311e72`.
- The complete tracked `custom_components/locklearn/` tree was deployed from
  the tested archive; 92 files were present. Rollback copies remain outside
  `/config/custom_components/`.
- HA restarted successfully. Config Entry is `loaded`, panel is `/locklearn`,
  schema is 5/WAL, integrity is `ok`, FK violations are zero and no
  LockLearn error/critical records are present.
- Local, CI and served panel bundle are identical: 304846 bytes,
  SHA-256 `2c9d2772b6b4049af1ba7349ebc074316cea7ddb977ee02d40d24c355ef62404`.
- Public real-HA P3.8 qualification passed: CAS/stale session, Undo,
  reconnect/reload and storage health. Targeted Beta.5 reminder/grading tests
  passed; real HA inventory remained healthy after cleanup.
- Temporary Advanced SSH and File editor add-ons were stopped and the temporary
  local SSH key was removed from the add-on configuration.

## Next action

This handoff update must be committed, pushed, CI-qualified and redeployed so
the final local/CI/HA SHA remains identical. Do not merge, tag or publish.
