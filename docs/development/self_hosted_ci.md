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
| Docker | aucun accès Docker accordé à LockLearn; Docker rootless ThermalTwin reste sous `tt-runner` |

Deux runners constituent le point de départ. Ils partagent le CPU, la mémoire,
le disque et l'I/O de la VM : ils ne constituent pas deux hôtes isolés. Les
benchmarks et les métriques de performance LockLearn sont donc des mesures de
VM partagée et ne remplacent pas une référence matérielle dédiée.

L'installation LockLearn ne lit pas `/home/tt-runner`, `/home/developer`, les
répertoires ThermalTwin, les fichiers `.env`, les clés SSH, les tokens HA ou un
socket Docker. `ll-runner` n'a pas de règle sudo et n'est pas membre du groupe
`docker`. Les services utilisent un compte distinct, des workspaces distincts
et `NoNewPrivileges`/protections systemd. Les connexions réseau sont sortantes
uniquement via le runner GitHub; aucun port entrant n'est ouvert.

## Événements et permissions GitHub

`.github/workflows/ci.yml` ne contient plus `pull_request`. Ses événements sont
les pushes vers `main`, `feat/**`, `fix/**`, `chore/**`, `docs/**`,
`refactor/**` et `test/**`, ainsi que `workflow_dispatch`. Ces branches ne
sont pas une autorisation GitHub en elles-mêmes : l'autorisation vient du droit
d'écriture sur `rfrachot/LockLearn`. Le dépôt doit conserver une protection de
`main` avec revue obligatoire et aucune écriture directe pour les contributeurs
externes.

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

L'installation initiale est volontairement explicite et ne met aucun jeton dans
Git. Les commandes suivantes sont des exemples opératoires; remplacer
`<version>` et générer un nouveau jeton d'enregistrement juste avant chaque
installation :

```bash
sudo useradd --create-home --home-dir /home/ll-runner --shell /usr/sbin/nologin ll-runner
sudo passwd --lock ll-runner
sudo loginctl enable-linger ll-runner
sudo install -d -o ll-runner -g ll-runner -m 0750 /home/ll-runner/actions
sudo install -d -o ll-runner -g ll-runner -m 0750 /home/ll-runner/.cache/{pip,npm,ms-playwright}

runner_token="$(gh api -X POST repos/rfrachot/LockLearn/actions/runners/registration-token --jq .token)"
sudo -u ll-runner -H env RUNNER_TOKEN="$runner_token" bash -c '
  set -euo pipefail
  mkdir -p "$HOME/actions/runner-1" && cd "$HOME/actions/runner-1"
  curl -fL -o runner.tar.gz \
    https://github.com/actions/runner/releases/download/v<version>/actions-runner-linux-x64-<version>.tar.gz
  tar -xzf runner.tar.gz && rm runner.tar.gz
  ./config.sh --unattended --url https://github.com/rfrachot/LockLearn \
    --token "$RUNNER_TOKEN" \
    --name locklearn-dev-1 --labels locklearn-dev --work _work --disableupdate
'
unset runner_token
```

Chaque service user systemd est installé dans
`~/.config/systemd/user/actions-runner-N.service` :

```ini
[Unit]
Description=GitHub Actions runner LockLearn N
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=%h/actions/runner-N
ExecStart=%h/actions/runner-N/run.sh
Restart=always
RestartSec=10
Nice=5
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
UMask=0077

[Install]
WantedBy=default.target
```

Activer et vérifier :

```bash
systemctl --user daemon-reload
systemctl --user enable --now actions-runner-1.service
systemctl --user status actions-runner-1.service
journalctl --user -u actions-runner-1.service --no-pager -n 100
gh api repos/rfrachot/LockLearn/actions/runners \
  --jq '.runners[]|[.name,.status,.busy]|@tsv'
```

Les dépendances OS Chromium sont installées une fois par l'administrateur de la
VM. Le workflow ne lance ensuite que `npx playwright install chromium` dans le
cache `ll-runner`; il ne demande pas de sudo depuis un job GitHub.

## Caches, concurrence et nettoyage

Les workflows utilisent les caches locaux `PIP_CACHE_DIR`,
`NPM_CONFIG_CACHE` et `PLAYWRIGHT_BROWSERS_PATH`. Les caches GitHub Actions de
`setup-python` ne sont pas utilisés. `requirements-dev.txt`, les versions HA
explicites, `frontend/package-lock.json` et `npm ci` restent les sources de
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
du -sh /home/ll-runner/.cache/pip /home/ll-runner/.cache/npm /home/ll-runner/.cache/ms-playwright
```

Ne jamais exécuter `docker system prune -af` sur la VM. LockLearn n'utilise pas
Docker; toute maintenance Docker concerne exclusivement le compte qui possède
le daemon et doit préserver ThermalTwin et le développement interactif. Les
anciens workspaces LockLearn peuvent être supprimés seulement après inspection
d'un runner arrêté et après confirmation qu'aucun job n'est actif.

## Diagnostic, arrêt et retrait

```bash
# depuis ll-runner avec XDG_RUNTIME_DIR=/run/user/$(id -u)
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

État avant installation, relevé le 9 octobre 2026 : dépôt public avec droit
administrateur pour le mainteneur; HEAD de développement `efa005e` sur
`feat/beta5-final-polish-v05`; VM Ubuntu x86_64, 12 vCPU, 64 Gio RAM; quatre
runners ThermalTwin actifs sous `tt-runner`; aucun runner LockLearn installé.

La validation finale doit publier ici, après exécution réelle :

- branche et SHA du commit de migration;
- nombre de runners LockLearn et services actifs;
- URLs des runs CI et durée de la campagne;
- résultat de chaque job backend, dataset, frontend, E2E et HA;
- preuve `runs-on` self-hosted et absence de compute GitHub-hosted;
- résultat du test de file d'attente runner arrêté puis de son redémarrage;
- statut de la protection fork et de l'environnement `dataset-release`;
- statut de la signature dataset;
- mesures CPU/RAM/disque et confirmation que ThermalTwin n'a pas été perturbé;
- limites ou vérifications restées `NON TESTÉES`.

Une vérification non exécutée est `NON TESTÉE`, jamais `PASS`. Le rollback des
workflows consiste à désactiver les services LockLearn, rétablir le dernier
workflow validé sur une branche protégée après revue, puis retirer les runners
avec `config.sh remove`; il ne faut pas basculer silencieusement vers
`ubuntu-latest`.
