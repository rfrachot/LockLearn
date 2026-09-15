---
description: Vérifie la branche et prépare une PR vers main ; --create autorise explicitement push + création GitHub.
argument-hint: [--create]
allowed-tools: Bash, Read, Task
---

# Principe

Par défaut, cette commande **prépare** la PR mais ne pousse rien.

Si et seulement si `$ARGUMENTS` contient `--create`, cela vaut demande explicite
de Renaud pour :

1. pousser la branche courante ;
2. créer la PR GitHub vers `main` avec `gh pr create` si `gh` est disponible.

Le merge reste toujours séparé et nécessite une demande explicite ultérieure.

# Vérifications

- branche différente de `main` ;
- worktree propre ou changements explicitement signalés ;
- diff contre `main`/`origin/main` ;
- aucun secret/fichier généré évident ;
- tests, Ruff et mypy selon `PROJECT.md` ;
- revue `review` si le changement n'est pas trivial.

Ne pas fetch/pull/rebase automatiquement pour « mettre à jour » la branche.

# Format proposé

Titre Conventional Commit court, puis corps :

```markdown
## Pourquoi
<problème / objectif>

## Changements
- ...

## Vérification
- `...` — OK/KO

## Risques / limites
- ...
```

Si `--create` n'est pas présent, s'arrêter après le texte et le verdict de
préparation.
