---
name: revue-pr
description: Auditer une PR ou un diff contre main comme second regard IA, sans modifier les fichiers.
allowed-tools: Bash, Read, Grep, Glob, Task
---

# Revue PR

Cette revue remplace le réflexe « une autre personne doit relire » par un second
regard IA + CI, adapté à un développeur solo.

Ne modifier aucun fichier.

## Périmètre

Comparer la branche à `main`/`origin/main` disponible localement. Si la base est
manifestement ancienne, le signaler mais ne pas fetch/pull sans demande.

Vérifier en priorité :

- comportement incorrect ou cas limite oublié ;
- régression ;
- erreur de gestion de données, ressources ou concurrence ;
- secret ou effet distant involontaire ;
- contrat/API cassé ;
- test manquant sur une zone risquée ;
- complexité ajoutée sans bénéfice clair.

Déléguer `tests` et `quality` si leur résultat n'est pas déjà récent et fiable.

## Restitution

20 lignes environ maximum, triées par risque :

```text
AMPLEUR      : <fichiers/lignes>
VERIFICATION : tests <...> / qualité <...>
BLOQUANTS    : <0 à 3>
- <chemin>:<ligne> — <constat>
A DISCUTER   : <0 à 3>
- <constat>
A VERIFIER MANUELLEMENT : <si nécessaire>
VERDICT      : prêt | corrections nécessaires | incomplet
```
