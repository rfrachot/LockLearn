# Codex — workflow LockLearn

Codex utilise `AGENTS.md` comme point d'entrée repo natif. Les instructions plus
profondes peuvent être placées dans des `AGENTS.md` de sous-répertoires si un
jour un sous-système exige des règles réellement différentes.

Pour LockLearn, ne crée pas de seconde vérité Codex :

1. lire `AGENTS.md` ;
2. lire `SPEC_V1.md` pour toute décision produit/architecture ;
3. lire `PROJECT.md` pour les faits d'environnement ;
4. lire `AGENT_HANDOFF.md` et la mission active ;
5. n'ouvrir que les ADR/code/tests pertinents.

## Délégation / sous-agents

Quand l'interface Codex courante permet la délégation, utiliser des sous-agents
pour des tâches bornées et en lecture seule autant que possible :

- **explore** — cartographier un point précis du dépôt ;
- **tests** — exécuter les vérifications ciblées et résumer les échecs ;
- **quality** — Ruff/mypy/TypeScript sans correction automatique ;
- **review** — relire le diff contre `main` et signaler les risques.

Ces noms décrivent des rôles de travail partagés avec Claude Code ; ils ne
supposent pas un format de fichier Codex propriétaire. Les missions dans
`missions/` restent le format portable entre les deux IAs.

## Git

Codex peut modifier, tester et **commit localement**. Push, création/modification
de PR distante, merge, tag et release seulement sur demande explicite de Renaud,
conformément à `AGENTS.md`.

## Configuration locale

Les préférences Codex propres à la machine/utilisateur restent dans le
`config.toml` du `CODEX_HOME` et ne doivent pas devenir une configuration projet
opaque. Les contraintes partagées et versionnées appartiennent à `AGENTS.md` et
aux documents du dépôt.

## Handoff

Avant de céder la main à Claude Code ou à une nouvelle session Codex, mettre à
jour `AGENT_HANDOFF.md` avec : branche, mission, dernier commit, tests réellement
exécutés, risques et prochaine action concrète.
