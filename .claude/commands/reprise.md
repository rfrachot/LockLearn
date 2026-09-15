---
description: Reprend l'état partagé laissé par Claude Code ou Codex sans relire inutilement tout le dépôt.
argument-hint: [mission]
allowed-tools: Bash, Read, Glob
---

# Rôle

Restituer l'état avant d'agir.

1. Lire `AGENT_HANDOFF.md`.
2. Vérifier `git status --short` et la branche courante.
3. Lire la mission indiquée dans le handoff, ou celle passée en argument.
4. Lire seulement la partie nécessaire de `PROJECT.md` / `MASTER_PLAN.md`.
5. Signaler immédiatement tout écart entre le handoff et le worktree.

# Retour

```text
MISSION      : <id/titre ou aucune>
STATUT       : <idle/en cours/bloqué/terminé>
BRANCHE      : <branche>
ECART GIT    : <aucun ou constat>
VERIFICATION : <dernier état connu, clairement daté/repris>
RESTE        : <5 puces max>
QUESTION     : <si décision humaine attendue>
PREMIERE ACTION : <une ligne>
```

Ne pas reprendre automatiquement une tâche bloquée par une décision de Renaud.
Si tout est clair et non bloqué, la restitution peut être suivie de l'action
seulement si la demande de l'utilisateur était explicitement de continuer.
