# Claude Code

`AGENTS.md` est la source de vérité commune à Claude Code et Codex. Lis-le et
respecte-le avant toute modification substantielle.

Pour le contexte propre au projet, utilise ensuite uniquement ce qui est utile :
`PROJECT.md`, `AGENT_HANDOFF.md`, la mission active dans `missions/`, puis la
section pertinente de `MASTER_PLAN.md`.

Ne duplique pas l'état du projet dans ce fichier : il doit rester un point
d'entrée Claude très léger.

## Outils Claude disponibles

- sous-agents : `explore`, `tests`, `quality`, `review`, basés sur les rôles partagés de `.ai/agents/` ;
- commandes : `/init-projet`, `/mission`, `/handoff`, `/reprise`, `/pr` ;
- skills : `nouveau-projet`, `revue-pr`, `livraison`, `doc-technique`.

Les quatre sous-agents utilisent explicitement **Haiku**. Utilise-les pour isoler
les explorations ou sorties volumineuses, mais garde les décisions et la
modification principale dans la session qui porte la tâche. Ne délègue pas une
commande triviale juste pour déléguer.

Les règles Git d'`AGENTS.md` s'appliquent aussi ici : commits locaux autorisés ;
push, PR distante, merge, tag et publication uniquement sur demande explicite.
