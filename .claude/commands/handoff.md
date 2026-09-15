---
description: Met à jour AGENT_HANDOFF.md pour passer proprement à une autre session ou à l'autre IA.
argument-hint: [mission]
allowed-tools: Bash, Read, Write, Edit
---

# État à relever

- `git status --short`
- branche courante
- dernier commit local pertinent
- mission active, si elle existe
- vérifications réellement exécutées pendant la session

# Rôle

Mettre à jour **le fichier racine `AGENT_HANDOFF.md`**. Ne pas seulement afficher
un résumé.

Le fichier doit rester une photographie courte de l'état courant. Remplacer les
sections obsolètes ; ne pas empiler un journal chronologique.

Si des changements sont non committés ou non vérifiés, l'écrire en premier dans
`Modifications non terminées` avec les chemins concernés et ce qu'il reste à
faire.

# Contenu attendu

- date/heure approximative et agent si connu ;
- branche et mission ;
- dernier commit lié ;
- travail terminé récemment ;
- modifications non terminées ;
- vérifications avec verdicts réels ;
- prochaine action concrète ;
- questions qui attendent Renaud ;
- pièges/contexte à ne pas perdre.

Ne jamais écrire « tests OK » s'ils n'ont pas été exécutés.
Ne pas pousser, merger ou taguer pendant un handoff.
