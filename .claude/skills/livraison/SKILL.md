---
name: livraison
description: Préparer une version ou release Python : vérifications, changelog, version et gestes de publication restant à autoriser.
allowed-tools: Bash, Read, Write, Edit, Task
---

# Préparer une livraison

Préparer ne veut pas dire publier.

## Contrôles

- branche et worktree cohérents ;
- CI locale pertinente : tests, Ruff, mypy ;
- changelog/documentation à jour si le changement le justifie ;
- version actuelle et incrément proposé ;
- procédure d'installation ou migration si nécessaire ;
- limites connues explicites.

Sémantique de version par défaut : SemVer si le projet utilise des versions.
Ne pas introduire SemVer dans un script jetable qui n'a pas de concept de
release.

## Actions distantes

Ne pas pousser, merger, taguer, publier sur PyPI/GitHub ou créer une release sans
demande explicite de Renaud.

Si la demande autorise la publication, effectuer uniquement les gestes demandés
et vérifier leur résultat.

## Retour

État des vérifications, version proposée, changements utilisateur, risques et
liste exacte des actions distantes encore non exécutées.
