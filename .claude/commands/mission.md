---
description: Crée ou révise une mission bornée partageable entre Claude Code et Codex.
argument-hint: <nom-court ou identifiant>
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Objectif

Créer une mission `missions/M-xxx-<nom>.md` qui puisse être exécutée par Claude
Code ou Codex sans dépendre de la conversation actuelle.

# Déroulé

1. Lire `PROJECT.md`, la partie pertinente de `MASTER_PLAN.md` et
   `AGENT_HANDOFF.md` si un travail est en cours.
2. Réutiliser un fichier de mission existant si l'argument le désigne clairement.
3. Sinon choisir le prochain identifiant `M-xxx` disponible.
4. Écrire : objectif observable, contexte minimal, périmètre, hors périmètre,
   critères d'acceptation, vérifications et état.
5. Si un choix important manque, demander à Renaud avant de figer la mission.

Ne pas transformer la mission en spécification exhaustive. Elle doit être assez
précise pour éviter les suppositions, mais assez courte pour rester lisible.
