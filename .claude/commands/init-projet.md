---
description: Initialise ou remet à niveau le contexte projet partagé par Claude Code et Codex.
argument-hint: [--revoir]
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# Objectif

Rendre `PROJECT.md`, `MASTER_PLAN.md` et `AGENT_HANDOFF.md` suffisamment fiables
pour qu'une autre IA puisse travailler sans la conversation actuelle.

Ne pas inventer les informations manquantes.

# Détection

Commencer par :

- `git status --short`
- branche courante ;
- fichiers Python et points d'entrée visibles ;
- `pyproject.toml`, `requirements*.txt`, `.python-version` s'ils existent ;
- commandes de test/CI déjà présentes ;
- README et documentation d'architecture uniquement s'ils semblent pertinents.

Ne pas lire tout le dépôt. Utiliser `explore` si l'inventaire dépasse une petite
poignée de fichiers.

# Python

Projet existant : respecter la version et les outils déclarés.

Nouveau projet sans contrainte : déterminer la version stable de CPython la plus
récente déjà installée sur la machine. Ne pas installer de nouvelle version.
Proposer d'enregistrer le `major.minor` dans `.python-version`.

Si `.venv` n'existe pas, proposer/faire sa création seulement si cela correspond
à la demande actuelle. Ne pas installer silencieusement des dépendances réseau.

# Questions

Après inspection, poser uniquement les questions dont la réponse change
réellement le projet : objectif, comportement attendu, matériel/API externe,
contraintes de déploiement, compatibilité, etc.

Regrouper les questions liées. Ne pas demander à Renaud ce que le dépôt montre
déjà.

# Écriture

Une fois les faits établis :

1. mettre à jour `PROJECT.md` avec les faits stables et commandes réellement
   vérifiées ;
2. adapter `MASTER_PLAN.md` au vrai projet sans créer de phases artificielles ;
3. remettre `AGENT_HANDOFF.md` dans un état cohérent ;
4. ne pas modifier le code applicatif sauf demande explicite.

Avec `--revoir`, auditer aussi les trois fichiers pour retirer les informations
obsolètes ou dupliquées.

# Retour

Résumé court : Python retenu, commandes vérifiées, contexte complété, inconnues
restantes et prochaine action proposée.
