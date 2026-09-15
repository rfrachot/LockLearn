---
name: nouveau-projet
description: Cadrer et démarrer un nouveau projet Python simple, testable et compatible avec le workflow Claude Code/Codex.
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Nouveau projet Python

Commencer par le besoin, pas par l'arborescence.

## Avant le code

Établir seulement les informations qui changent la solution :

- objectif et utilisateur du programme ;
- CLI, service, bibliothèque, automatisation ou autre forme ;
- systèmes externes / matériel ;
- contraintes de déploiement ;
- données sensibles ou irréversibles ;
- besoin de persistance/concurrence/performance inhabituel.

Si une réponse essentielle manque, la demander.

## Socle

- dernière version stable de CPython déjà installée et compatible ;
- `.venv` + pip ;
- Ruff + mypy + pytest ;
- `.python-version` avec `major.minor` ;
- structure minimale qui fonctionne.

Exemples, pas obligations :

- petit script : quelques modules à la racine peuvent suffire ;
- application réutilisable : `src/<package>/` + `tests/` ;
- service : séparer domaine et I/O seulement là où c'est utile aux tests.

Ne pas créer repository pattern, dependency injection framework, plugin system ou
couches génériques sans besoin démontré.

## Après cadrage

1. compléter `PROJECT.md` ;
2. simplifier `MASTER_PLAN.md` au vrai projet ;
3. créer la première mission si le travail dépasse une courte session ;
4. écrire le plus petit squelette exécutable ;
5. ajouter au moins une vérification utile ;
6. lancer les contrôles ;
7. commit local.

Un framework ou une dépendance structurante se propose à Renaud avant adoption.
