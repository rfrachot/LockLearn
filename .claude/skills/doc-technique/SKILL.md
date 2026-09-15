---
name: doc-technique
description: Mettre à jour la documentation technique Python sans recopier le code ni inventer l'architecture.
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Documentation technique

Documenter ce qu'un futur Renaud ou une future IA ne déduira pas facilement du
code.

Priorités :

- `PROJECT.md` pour les commandes, contraintes et systèmes externes ;
- `docs/architecture.md` si l'architecture mérite une vue dédiée ;
- `docs/decisions/` pour les choix durables non évidents ;
- docstrings pour les contrats publics et comportements subtils ;
- README pour installation et usage humain.

Ne pas écrire une page qui paraphrase chaque classe/fonction.

Pour une nouvelle documentation générée, Sphinx est un candidat naturel dans les
projets qui en ont réellement besoin, mais ne pas l'ajouter à un petit outil sans
bénéfice clair. Respecter l'outil déjà choisi par le projet.
