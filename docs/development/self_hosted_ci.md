# CI LockLearn sur runners self-hosted

## Décision et périmètre

La CI normale de LockLearn s'exécute sur la VM Ubuntu de développement avec des
runners GitHub Actions dédiés. La migration change le lieu d'exécution, pas les
contrôles : les suites backend, datasets, Home Assistant, frontend, E2E,
performance, documentation et release restent bloquantes.

Le dépôt reste public. Pour cette raison, aucun événement `pull_request` ne
est attaché aux runners persistants LockLearn. Les workflows sont déclenchés
par des pushes sur `main` et sur les familles de branches internes autorisées,
ou par `workflow_dispatch`. Un fork externe ne peut pas pousser dans ces
branches et ne déclenche donc pas la CI self-hosted. Une PR externe ne reçoit
pas de checkout ni d'exécution sur cette VM. Une vérification PR externe doit
utiliser un mécanisme éphémère séparé si elle est ajoutée plus tard.

Si la VM est arrêtée ou si les runners sont hors ligne, GitHub laisse les jobs
en file d'attente. Il n'existe aucun fallback `ubuntu-latest`.

## Architecture installée

| Élément | LockLearn |
|---|---|
| Hôte | VM Ubuntu x86_64, 12 vCPU, environ 60 Gio RAM |
| Compte | `ll-runner`, non root, mot de passe verrouillé, shell non interactif |
| Runners initiaux | `locklearn-dev-1`, `locklearn-dev-2` |
| Labels | `self-hosted`, `Linux`, `X64`, `locklearn-dev` |
| Installation | `/home/ll-runner/actions/runner-{1,2}` |
| Workspaces | `/home/ll-runner/actions/runner-{1,2}/_work` |
| Services | `actions-runner-1.service`, `actions-runner-2.service` (user systemd) |
| Caches | `/home/ll-runner/.cache/{pip,npm,ms-playwright}` |
| Docker | Docker rootless privé à `ll-runner`, socket `/run/user/<uid>/docker.sock`; le Docker de `tt-runner` et le socket rootful restent hors périmètre |

Deux runners constituent le point de départ. Ils partagent le CPU, la mémoire,
le disque et l'I/O de la VM : ils ne constituent pas deux hôtes isolés. Les
benchmarks et les métriques de performance LockLearn sont donc des mesures de
VM partagée et ne remplacent pas une référence matérielle dédiée.

L'installation LockLearn ne lit pas `/home/tt-runner`, `/home/developer`, les
répertoires ThermalTwin, les fichiers `.env`, les clés SSH ou les tokens HA.
`ll-runner` n'a pas de règle sudo et n'est pas membre du groupe rootful
`docker`. Les deux services runners héritent explicitement de
`DOCKER_HOST=unix:///run/user/<uid>/docker.sock`; ils ne peuvent donc pas
utiliser le socket `/var/run/docker.sock`. Le daemon rootless, son stockage et
son socket appartiennent à `ll-runner` et sont distincts de ceux de `tt-runner`.
Les services utilisent un compte distinct, des workspaces distincts et
`NoNewPrivileges` et d'un compte sans privilège. Les restrictions systemd
de namespaces/seccomp incompatibles avec un user manager non privilégié ne
sont pas utilisées, afin que l'extraction des actions GitHub reste
fonctionnelle. Les connexions réseau sont sortantes uniquement via le runner
GitHub; aucun port entrant n'est ouvert.

## Événements et permissions GitHub

`.github/workflows/ci.yml` ne contient plus `pull_request`. Ses événements sont
les pushes vers `main`, `feat/**`, `fix/**`, `chore/**`, `docs/**`,
`refactor/**` et `test/**`, ainsi que `workflow_dispatch`. Ces branches ne
sont pas une autorisation GitHub en elles-mêmes : l'autorisation vient du droit
d'écriture sur `rfrachot/LockLearn`. Le dépôt doit conserver une protection de
`main` est protégée par revue obligatoire pour les pushes non administrateurs,
résolution des conversations, interdiction du force-push et de la suppression.
Les administrateurs peuvent encore publier directement en cas d'urgence; cette
exception est volontairement réservée au mainteneur.

Les permissions par défaut sont `contents: read`. Le job `manual-build` de
`.github/workflows/datasets.yml` est le seul job demandant `contents: write`;
il est limité à `workflow_dispatch` depuis `refs/heads/main`, après la
validation sans secret. Les inputs sont transmis au shell via des variables
d'environnement et jamais interpolés directement dans une commande.

La clé `LOCKLEARN_DATASET_SIGNING_KEY_B64` n'est jamais écrite sur le disque.
Elle doit être stockée comme secret de l'environnement GitHub protégé
`dataset-release`, avec approbation explicite du mainteneur, puis retirée des
secrets de dépôt si elle y était précédemment configurée. Aucun job ordinaire,
aucune validation planifiée et aucune PR externe ne reçoit cette clé. Une
publication signée ne doit être lancée qu'après vérification de la branche, de
l'environnement et du diff de contenu.

Commandes de vérification GitHub (à exécuter avec un compte administrateur) :

```bash
gh repo view rfrachot/LockLearn --json visibility,viewerPermission
gh api repos/rfrachot/LockLearn/actions/permissions
gh api repos/rfrachot/LockLearn/actions/runners \
  --jq '.runners[]|[.name,.status,(.labels|map(.name)|join(","))]|@tsv'
gh api repos/rfrachot/LockLearn/branches/main/protection
gh secret list --repo rfrachot/LockLearn
gh secret list --env dataset-release --repo rfrachot/LockLearn
```

Le réglage Actions doit rester en lecture pour `GITHUB_TOKEN` et demander une
approbation pour les contributeurs externes. Ne pas activer de mécanisme
`pull_request_target`, `workflow_run` ou autre pont qui ferait entrer du code
de fork sur ces runners.

## Installation et services

Le bootstrap auditable est versionné dans
`scripts/bootstrap-self-hosted-ci.sh`. Il doit être exécuté une seule fois
depuis une session SSH interactive, après revue, avec le `sudo` de la session :

```bash
sudo ./scripts/bootstrap-self-hosted-ci.sh --repo rfrachot/LockLearn
```

Le script ne reçoit ni mot de passe sudo ni secret GitHub. Il utilise la session
`gh` authentifiée de l'utilisateur qui a lancé `sudo`, demande des jetons
d'enregistrement éphémères uniquement si un runner manque, les transmet en
mémoire à `config.sh`, puis les efface. L'archive du runner est vérifiée par
SHA-256 avant extraction. Une réexécution est sans effet sur les runners déjà
enregistrés et refuse les installations partielles ou enregistrées vers un
autre dépôt.

Le script installe `ll-runner`, les plages `/etc/subuid`/`/etc/subgid`, les
prérequis rootless et les bibliothèques système Chromium. Il ne met pas à jour,
n'arrête pas, ne désactive pas et ne reconfigure pas le Docker existant. Le
daemon rootless LockLearn est installé comme service utilisateur
`docker.service` sous `ll-runner`, avec son propre stockage et
`/run/user/<uid>/docker.sock`. Les services
`actions-runner-{1,2}.service` en dépendent et fixent leur `DOCKER_HOST` sur ce
socket. `ll-runner` reste hors des groupes `docker` et `sudo`.

Vérifier après installation :

```bash
sudo -u ll-runner -H env XDG_RUNTIME_DIR=/run/user/$(id -u ll-runner) \
  DOCKER_HOST=unix:///run/user/$(id -u ll-runner)/docker.sock \
  docker info --format '{{.DockerRootDir}}'
sudo -u ll-runner -H env XDG_RUNTIME_DIR=/run/user/$(id -u ll-runner) \
  systemctl --user status docker.service actions-runner-{1,2}.service
gh api repos/rfrachot/LockLearn/actions/runners \
  --jq '.runners[]|[.name,.status,.busy,(.labels|map(.name)|join(","))]|@tsv'
```

Les dépendances OS Chromium sont installées une fois par l'administrateur de la
VM. Le workflow ne lance ensuite que `npx playwright install chromium` dans le
cache `ll-runner`; il ne demande pas de sudo depuis un job GitHub.

## Caches, concurrence et nettoyage

Les workflows utilisent le cache pip persistant local `PIP_CACHE_DIR`; les
caches npm et Playwright sont propres à chaque étape frontend sous
`runner.temp`, afin qu'aucun fichier root-owned historique ne puisse
contaminer un job frontend.
Les caches GitHub Actions de `setup-python` ne sont pas utilisés. Chaque job
Python crée un venv neuf sous `RUNNER_TEMP` après `setup-python`; aucun paquet
Python ne s'installe dans le site global ou dans un autre job.
`requirements-dev.txt`, les versions HA explicites,
`frontend/package-lock.json` et `npm ci` restent les sources de
reproductibilité.

Les jobs sont limités à deux exécutions simultanées par la capacité actuelle.
La concurrence par référence annule un run obsolète de la même branche; elle ne
permet jamais un fallback hébergé. Les jobs HA ont des timeouts explicites et la
matrice minimum/current/latest est inchangée. Les performances sont conservées,
mais leur résultat doit être lu comme télémétrie d'une VM partagée.

Observer l'espace avant tout nettoyage :

```bash
df -h /
du -sh /home/ll-runner/actions/*/_work 2>/dev/null
du -sh /home/ll-runner/.cache/pip
```

Ne jamais exécuter `docker system prune -af` sur la VM. Toute maintenance du
daemon rootless LockLearn doit être lancée sous `ll-runner` et ne doit jamais
viser le daemon ou les caches de ThermalTwin. Les anciens workspaces LockLearn
peuvent être supprimés seulement après inspection d'un runner arrêté et après
confirmation qu'aucun job n'est actif.

## Diagnostic, arrêt et retrait

```bash
# depuis ll-runner avec XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user status docker.service
systemctl --user status actions-runner-{1,2}.service
systemctl --user restart actions-runner-1.service
systemctl --user stop actions-runner-{1,2}.service
journalctl --user -u actions-runner-1.service --since today --no-pager
gh run list --repo rfrachot/LockLearn --limit 20
```

Pour désactiver LockLearn sans toucher ThermalTwin :

```bash
sudo -u ll-runner -H env XDG_RUNTIME_DIR=/run/user/$(id -u ll-runner) \
  systemctl --user disable --now actions-runner-{1,2}.service
sudo -u ll-runner -H env XDG_RUNTIME_DIR=/run/user/$(id -u ll-runner) \
  systemctl --user disable --now docker.service
```

Pour un retrait propre, obtenir un jeton éphémère puis retirer chaque runner
avant de supprimer ses fichiers :

```bash
sudo -u ll-runner -H env XDG_RUNTIME_DIR=/run/user/$(id -u ll-runner) \
  systemctl --user disable --now actions-runner-1.service
cd /home/ll-runner/actions/runner-1
remove_token="$(gh api -X POST repos/rfrachot/LockLearn/actions/runners/remove-token --jq .token)"
sudo -u ll-runner -H env RUNNER_TOKEN="$remove_token" bash -c '
  cd /home/ll-runner/actions/runner-1
  ./config.sh remove --token "$RUNNER_TOKEN"
'
unset remove_token
rm /home/ll-runner/.config/systemd/user/actions-runner-1.service
sudo -u ll-runner -H env XDG_RUNTIME_DIR=/run/user/$(id -u ll-runner) systemctl --user daemon-reload
```

Répéter pour le runner 2, puis supprimer uniquement les répertoires LockLearn
identifiés. Ne pas toucher `/home/tt-runner`, ses services, son daemon Docker,
ses caches ni ses workspaces.

## Validation et état de cette migration

État relevé le 9 octobre 2026 :

- branche `chore/self-hosted-ci`, commit poussé `c569c03` avant la correction de revue;
- dépôt public, `GITHUB_TOKEN` par défaut en lecture, approbation des premiers
  contributeurs externes activée;
- `main` protégée par une approbation, résolution des conversations et
  interdiction du force-push/suppression;
- environnement `dataset-release` créé, lié aux branches protégées, avec revue
  obligatoire et auto-approbation interdite;
- quatre runners ThermalTwin actifs sous `tt-runner`; leur daemon, leurs
  services et leurs caches sont hors périmètre du bootstrap LockLearn;
- bootstrap `ll-runner`, Docker rootless dédié et deux services LockLearn :
  `NON TESTÉS` jusqu'à exécution interactive du script;
- run CI `37980380168` : `queued` sur le label `locklearn-dev`, preuve qu'aucun
  fallback GitHub-hosted n'est utilisé; jobs normaux et durée de campagne :
  `NON TESTÉS` tant qu'un runner dédié n'est pas installé;
- validations locales au commit : Ruff format/check, mypy, ressources, schémas,
  546 pytest, frontend lint/typecheck, 69 Vitest, no-polling, build et bundle;
- secret `LOCKLEARN_DATASET_SIGNING_KEY_B64` absent du dépôt et de
  l'environnement : publication signée `NON TESTÉE` et bloquée fail-closed;
- ressources VM observées : 12 vCPU, environ 64 Gio RAM, Docker rootless sous
  `tt-runner`; aucun service ThermalTwin n'a été modifié.

La campagne GitHub complète, le redémarrage d'un runner, le test d'isolement des
répertoires, la validation des venv par matrice et la non-régression ThermalTwin
restent `NON TESTÉS` jusqu'à l'installation. Ils devront être ajoutés ici avec
les URLs GitHub, les durées et les mesures réelles. La publication signée des
datasets reste `NON TESTÉE` tant que la clé n'est pas disponible et ne bloque
pas les jobs ordinaires.

Une vérification non exécutée est `NON TESTÉE`, jamais `PASS`. Le rollback des
workflows consiste à désactiver les services LockLearn, rétablir le dernier
workflow validé sur une branche protégée après revue, puis retirer les runners
avec `config.sh remove`; il ne faut pas basculer silencieusement vers
`ubuntu-latest`.
