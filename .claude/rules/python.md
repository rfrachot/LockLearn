---
paths:
  - "**/*.py"
  - "pyproject.toml"
  - "requirements*.txt"
  - ".python-version"
description: Règles Python complémentaires au socle partagé dans AGENTS.md.
---

# Python

`AGENTS.md` contient les choix de fond. Ce fichier précise seulement les réflexes
à appliquer quand une modification touche Python.

## Code

- Préférer du code lisible directement à une abstraction sophistiquée.
- Utiliser `pathlib` pour les chemins quand cela simplifie le code.
- Utiliser des context managers pour les ressources à fermer.
- Favoriser les dataclasses ou structures simples avant des hiérarchies de
  classes.
- Les effets de bord importants doivent être visibles dans l'API ; éviter les
  imports qui déclenchent du travail.
- Lever des exceptions précises. Un `except Exception` n'est acceptable qu'à une
  frontière de processus ou pour ajouter du contexte avant de relancer/traiter.
- `logging.getLogger(__name__)` dans les modules ; configuration du logging au
  point d'entrée.

## Typage

- Annotations sur API publiques, données structurantes et fonctions non
  triviales.
- Ne pas ajouter des annotations complexes qui rendent le code moins clair que
  le risque qu'elles couvrent.
- Préférer `Protocol` uniquement lorsqu'une vraie substitution/testabilité le
  justifie.
- `# type: ignore[code]` ciblé et commenté si la raison n'est pas évidente.

## Tests

- Tester le comportement observable et les cas limites pertinents.
- Isoler réseau, temps, fichiers et matériel quand cela rend le test déterministe.
- Préférer des fixtures petites et lisibles à de gros jeux de données opaques.
- Un bug corrigé mérite normalement un test de non-régression.

## Dépendances

- Respecter le gestionnaire existant ; pour un nouveau projet de ce template,
  `venv + pip` reste le défaut.
- Ne pas mettre à jour ou remplacer des dépendances sans lien avec la tâche.
- Une dépendance structurante ou lourde nécessite l'accord de Renaud.

## Vérification

Utiliser d'abord les commandes de `PROJECT.md`. À défaut :

```text
python -m ruff format --check .
python -m ruff check .
python -m mypy .
python -m pytest -q --tb=short
```

Pour corriger le format, `python -m ruff format <fichiers>` est autorisé sur le
périmètre concerné. Ne pas reformater gratuitement tout un dépôt existant si cela
pollue le diff.
