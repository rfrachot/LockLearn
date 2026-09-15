# Missions

Une mission est une unité de travail assez bornée pour être reprise par Claude
Code ou Codex sans relire toute la conversation d'origine.

Nom recommandé : `M-001-nom-court.md`, puis incrémenter.

## Modèle

```markdown
# M-001 — Titre

## Objectif
Résultat observable attendu.

## Contexte minimal
Faits nécessaires, liens vers PROJECT.md / MASTER_PLAN.md / décision.

## Périmètre
- ...

## Hors périmètre
- ...

## Critères d'acceptation
- [ ] ...

## Vérifications
- ...

## État
à faire | en cours | bloqué | terminé

## Notes de reprise
Seulement ce qui aide réellement l'agent suivant.
```

Éviter d'utiliser une mission comme journal détaillé. Le diff Git, les commits et
`AGENT_HANDOFF.md` portent déjà l'historique opérationnel.
