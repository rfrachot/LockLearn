#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# One-shot, rerunnable bootstrap for the dedicated LockLearn self-hosted CI
# account. The GitHub registration token is obtained from the invoking user's
# authenticated `gh` CLI and is kept in memory only; it is never written to a
# file or committed to the repository.

readonly RUNNER_USER="ll-runner"
readonly RUNNER_HOME="/home/${RUNNER_USER}"
readonly RUNNER_COUNT=2
readonly RUNNER_LABEL="locklearn-dev"
readonly RUNNER_ROOT="${RUNNER_HOME}/actions"
readonly CACHE_ROOT="${RUNNER_HOME}/.cache"
readonly RUNNER_BASE_URL="https://github.com/actions/runner/releases/download"

REPOSITORY="${LOCKLEARN_REPOSITORY:-rfrachot/LockLearn}"
RUNNER_VERSION="${LOCKLEARN_RUNNER_VERSION:-2.338.0}"
RUNNER_SHA256="${LOCKLEARN_RUNNER_SHA256:-af4b794c1bc41d73d40535e3fe092a39f9679cd8d965954c2aca25a05ca41d32}"

usage() {
  cat <<'EOF'
Usage: sudo ./scripts/bootstrap-self-hosted-ci.sh [--repo OWNER/REPOSITORY]

The command must be run once from an interactive SSH session. It provisions the
ll-runner account, rootless Docker, two repository runners, and user-level
systemd services. GitHub authentication is read from the invoking user's
authenticated `gh` CLI; no token or sudo password is accepted as an option.

Optional environment overrides for a reviewed runner release:
  LOCKLEARN_RUNNER_VERSION=...
  LOCKLEARN_RUNNER_SHA256=...
EOF
}

log() {
  printf '[locklearn-bootstrap] %s\n' "$*"
}

die() {
  printf '[locklearn-bootstrap] ERROR: %s\n' "$*" >&2
  exit 1
}

on_error() {
  local line="$1"
  printf '[locklearn-bootstrap] ERROR: command failed at line %s\n' "$line" >&2
}

trap 'on_error "$LINENO"' ERR

while (($# > 0)); do
  case "$1" in
    --repo)
      (($# >= 2)) || die "--repo requires OWNER/REPOSITORY"
      REPOSITORY="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ ${EUID} -eq 0 ]] || die "run this script with sudo from the interactive SSH session"
[[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != root ]] || die "SUDO_USER is missing; do not run this script from a root shell"
[[ -t 0 && -t 1 ]] || die "an interactive SSH terminal is required"
[[ "${REPOSITORY}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || die "invalid repository: ${REPOSITORY}"
[[ "${RUNNER_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "invalid runner version"
[[ "${RUNNER_SHA256}" =~ ^[[:xdigit:]]{64}$ ]] || die "invalid runner SHA-256"
[[ "$(uname -m)" == x86_64 ]] || die "this bootstrap currently supports x86_64 only"

readonly INVOKING_USER="${SUDO_USER}"
readonly INVOKING_HOME="$(getent passwd "${INVOKING_USER}" | cut -d: -f6)"
[[ -n "${INVOKING_HOME}" && -d "${INVOKING_HOME}" ]] || die "cannot resolve the invoking user's home"

command -v apt-get >/dev/null || die "apt-get is required"
command -v systemctl >/dev/null || die "systemctl is required"
command -v loginctl >/dev/null || die "loginctl is required"
command -v runuser >/dev/null || die "runuser is required"

if getent passwd "${RUNNER_USER}" >/dev/null; then
  existing_home="$(getent passwd "${RUNNER_USER}" | cut -d: -f6)"
  [[ "${existing_home}" == "${RUNNER_HOME}" ]] || die "${RUNNER_USER} exists with unexpected home ${existing_home}"
  log "account ${RUNNER_USER} already exists; reusing it"
else
  useradd --create-home --home-dir "${RUNNER_HOME}" --shell /usr/sbin/nologin "${RUNNER_USER}"
fi

usermod --shell /usr/sbin/nologin "${RUNNER_USER}"
passwd --lock "${RUNNER_USER}" >/dev/null

remove_membership() {
  local group="$1"
  if id -nG "${RUNNER_USER}" | tr ' ' '\n' | grep -Fxq "${group}"; then
    log "removing ${RUNNER_USER} from ${group}; rootful Docker access is not permitted"
    gpasswd --delete "${RUNNER_USER}" "${group}" >/dev/null
  fi
}

remove_membership docker
remove_membership sudo

if grep -R -Eqs "^[[:space:]]*${RUNNER_USER}[[:space:]]" /etc/sudoers /etc/sudoers.d 2>/dev/null; then
  die "an existing sudoers rule grants ${RUNNER_USER} privilege; remove it manually before retrying"
fi

log "installing non-Docker system prerequisites"
apt-get update

base_packages=(
  ca-certificates curl dbus-user-session fuse-overlayfs gh git jq tar unzip xz-utils
  uidmap slirp4netns python3 python3-venv build-essential
  libffi-dev libssl-dev pkg-config
)

choose_package() {
  local candidate
  for candidate in "$@"; do
    if apt-cache show "${candidate}" >/dev/null 2>&1; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  die "none of the package alternatives is available: $*"
}

# Playwright's Chromium is downloaded by the job into ll-runner's cache. These
# are only its host libraries; no browser or npm tree is installed as root.
base_packages+=(
  "$(choose_package libasound2t64 libasound2)"
  "$(choose_package libatk-bridge2.0-0t64 libatk-bridge2.0-0)"
  "$(choose_package libatk1.0-0t64 libatk1.0-0)"
  "$(choose_package libcups2t64 libcups2)"
  "$(choose_package libglib2.0-0t64 libglib2.0-0)"
  libatspi2.0-0 libcairo2 libdbus-1-3 libdrm2 libgbm1 libnspr4 libnss3
  libpango-1.0-0 libwayland-client0 libx11-6 libx11-xcb1 libxcb1
  libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2
  xvfb fonts-noto-cjk
)

missing_packages=()
for package in "${base_packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "${package}" 2>/dev/null | grep -Fq 'install ok installed'; then
    missing_packages+=("${package}")
  fi
done
if ((${#missing_packages[@]})); then
  apt-get install -y --no-install-recommends "${missing_packages[@]}"
else
  log "system prerequisites already installed"
fi

# Never replace or upgrade the Docker installation that may belong to
# ThermalTwin. The target VM is expected to have Docker CE already; if its
# matching rootless extras are missing, install only that exact version.
if ! command -v docker >/dev/null 2>&1; then
  die "Docker CLI is absent; install the host's reviewed Docker CE bundle before retrying (no rootful daemon is installed by this script)"
fi

if ! command -v dockerd-rootless-setuptool.sh >/dev/null 2>&1; then
  docker_ce_version="$(dpkg-query -W -f='${Version}' docker-ce 2>/dev/null || true)"
  [[ -n "${docker_ce_version}" ]] || die "matching Docker rootless extras are unavailable without altering the existing Docker installation"
  apt-cache show "docker-ce-rootless-extras=${docker_ce_version}" >/dev/null 2>&1 \
    || die "docker-ce-rootless-extras ${docker_ce_version} is not available; install the matching package manually and retry"
  apt-get install -y --no-install-recommends --no-upgrade "docker-ce-rootless-extras=${docker_ce_version}"
fi

command -v dockerd-rootless-setuptool.sh >/dev/null || die "dockerd-rootless-setuptool.sh is still unavailable"
command -v dockerd-rootless.sh >/dev/null || die "dockerd-rootless.sh is still unavailable"
command -v newuidmap >/dev/null || die "newuidmap is required for rootless Docker"
command -v newgidmap >/dev/null || die "newgidmap is required for rootless Docker"

SUBID_COUNT=65536
subid_has_capacity() {
  local file="$1"
  awk -F: -v user="${RUNNER_USER}" -v count="${SUBID_COUNT}" \
    '$1 == user && $3 >= count { found = 1 } END { exit(found ? 0 : 1) }' "${file}" 2>/dev/null
}

subid_range_is_free() {
  local file="$1" start="$2" end="$3"
  awk -F: -v start="${start}" -v end="${end}" \
    '($2 <= end && ($2 + $3 - 1) >= start) { occupied = 1 } END { exit(occupied ? 1 : 0) }' \
    "${file}" 2>/dev/null
}

if ! subid_has_capacity /etc/subuid || ! subid_has_capacity /etc/subgid; then
  subid_start=1000000
  while :; do
    subid_end=$((subid_start + SUBID_COUNT - 1))
    if subid_range_is_free /etc/subuid "${subid_start}" "${subid_end}" \
      && subid_range_is_free /etc/subgid "${subid_start}" "${subid_end}"; then
      break
    fi
    subid_start=$((subid_start + SUBID_COUNT))
  done
  if ! subid_has_capacity /etc/subuid; then
    usermod --add-subuids "${subid_start}-${subid_end}" "${RUNNER_USER}"
  fi
  if ! subid_has_capacity /etc/subgid; then
    usermod --add-subgids "${subid_start}-${subid_end}" "${RUNNER_USER}"
  fi
fi

install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0750 "${RUNNER_ROOT}"
for cache_dir in "${CACHE_ROOT}/pip" "${CACHE_ROOT}/npm" "${CACHE_ROOT}/ms-playwright"; do
  install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0750 "${cache_dir}"
  # Persistent caches may contain files from an earlier administrator run.
  # Repair ownership before exposing them to the unprivileged runner.
  chown -R "${RUNNER_USER}:${RUNNER_USER}" "${cache_dir}"
done

RUNNER_UID="$(id -u "${RUNNER_USER}")"
readonly RUNNER_UID
readonly RUNTIME_DIR="/run/user/${RUNNER_UID}"

log "enabling linger and the ${RUNNER_USER} user manager"
loginctl enable-linger "${RUNNER_USER}"
systemctl start "user@${RUNNER_UID}.service"

as_runner() {
  runuser -u "${RUNNER_USER}" -- env \
    HOME="${RUNNER_HOME}" \
    XDG_RUNTIME_DIR="${RUNTIME_DIR}" \
    DBUS_SESSION_BUS_ADDRESS="unix:path=${RUNTIME_DIR}/bus" \
    "$@"
}

[[ -d "${RUNTIME_DIR}" ]] || die "user runtime directory is unavailable: ${RUNTIME_DIR}"

log "installing the dedicated rootless Docker user service"
as_runner env -u DOCKER_HOST -u DOCKER_CONTEXT dockerd-rootless-setuptool.sh --force install
as_runner systemctl --user enable --now docker.service

rootful_docker_state="$(systemctl is-active docker.service 2>/dev/null || true)"
rootful_socket_owner="$(stat -c '%u:%g' /var/run/docker.sock 2>/dev/null || true)"
log "leaving rootful Docker untouched (service=${rootful_docker_state:-unknown}, socket-owner=${rootful_socket_owner:-absent})"

rootless_docker_host="unix://${RUNTIME_DIR}/docker.sock"
docker_ready=false
for _ in $(seq 1 60); do
  if as_runner env DOCKER_HOST="${rootless_docker_host}" docker info --format '{{.DockerRootDir}}' >/dev/null 2>&1; then
    docker_ready=true
    break
  fi
  sleep 1
done
[[ "${docker_ready}" == true ]] || die "the dedicated rootless Docker daemon did not become ready"

rootless_root="$(as_runner env DOCKER_HOST="${rootless_docker_host}" docker info --format '{{.DockerRootDir}}')"
[[ "${rootless_root}" == "${RUNNER_HOME}"/* ]] || die "rootless Docker root is not private to ${RUNNER_HOME}: ${rootless_root}"
[[ "$(stat -c '%U' "${RUNTIME_DIR}/docker.sock")" == "${RUNNER_USER}" ]] || die "rootless Docker socket has the wrong owner"

archive=""
cleanup() {
  rm -f -- "${archive:-}"
  unset REGISTRATION_TOKEN
}
trap cleanup EXIT

runner_needs_registration=false
for index in $(seq 1 "${RUNNER_COUNT}"); do
  runner_dir="${RUNNER_ROOT}/runner-${index}"
  if [[ -f "${runner_dir}/.runner" ]]; then
    configured_url="$(jq -r '.gitHubUrl // .serverUrl // empty' "${runner_dir}/.runner" 2>/dev/null || true)"
    [[ "${configured_url}" == "https://github.com/${REPOSITORY}" ]] \
      || die "${runner_dir} is registered to ${configured_url:-an unknown URL}; remove it explicitly before retrying"
    [[ -x "${runner_dir}/run.sh" ]] || die "${runner_dir} is configured but run.sh is missing"
    log "runner ${index} already configured"
  else
    [[ ! -e "${runner_dir}" || -z "$(find "${runner_dir}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]] \
      || die "${runner_dir} contains an unconfigured partial installation"
    runner_needs_registration=true
  fi
done

if [[ "${runner_needs_registration}" == true ]]; then
  archive="$(mktemp --tmpdir=/var/tmp locklearn-actions-runner.XXXXXX.tar.gz)"
  runner_archive_url="${RUNNER_BASE_URL}/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
  log "downloading and verifying GitHub Actions runner ${RUNNER_VERSION}"
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --retry 3 --output "${archive}" "${runner_archive_url}"
  printf '%s  %s\n' "${RUNNER_SHA256}" "${archive}" | sha256sum --check --status - \
    || die "runner archive SHA-256 verification failed"
  command -v gh >/dev/null 2>&1 || die "gh is required for an authenticated registration-token request"
  log "requesting an ephemeral registration token through ${INVOKING_USER}'s gh session"
  REGISTRATION_TOKEN="$(runuser -u "${INVOKING_USER}" -- env HOME="${INVOKING_HOME}" \
    gh api -X POST "repos/${REPOSITORY}/actions/runners/registration-token" --jq .token)"
  [[ -n "${REGISTRATION_TOKEN}" ]] || die "GitHub returned an empty registration token"
fi

for index in $(seq 1 "${RUNNER_COUNT}"); do
  runner_dir="${RUNNER_ROOT}/runner-${index}"
  if [[ -f "${runner_dir}/.runner" ]]; then
    continue
  fi
  runner_name="locklearn-dev-${index}"
  log "configuring ${runner_name}"
  install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0750 "${runner_dir}"
  tar --extract --file "${archive}" --directory "${runner_dir}" --no-same-owner
  chown -R "${RUNNER_USER}:${RUNNER_USER}" "${runner_dir}"
  as_runner "${runner_dir}/config.sh" --unattended \
    --url "https://github.com/${REPOSITORY}" \
    --token "${REGISTRATION_TOKEN}" \
    --name "${runner_name}" \
    --labels "${RUNNER_LABEL}" \
    --work _work \
    --disableupdate
  unset REGISTRATION_TOKEN
  if ((index < RUNNER_COUNT)); then
    REGISTRATION_TOKEN="$(runuser -u "${INVOKING_USER}" -- env HOME="${INVOKING_HOME}" \
      gh api -X POST "repos/${REPOSITORY}/actions/runners/registration-token" --jq .token)"
    [[ -n "${REGISTRATION_TOKEN}" ]] || die "GitHub returned an empty registration token"
  fi
done

systemd_user_dir="${RUNNER_HOME}/.config/systemd/user"
install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0700 "${systemd_user_dir}"
for index in $(seq 1 "${RUNNER_COUNT}"); do
  runner_dir="${RUNNER_ROOT}/runner-${index}"
  unit_file="${systemd_user_dir}/actions-runner-${index}.service"
  tmp_unit="$(mktemp)"
  cat >"${tmp_unit}" <<EOF
[Unit]
Description=GitHub Actions runner LockLearn ${index}
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=${runner_dir}
ExecStart=${runner_dir}/run.sh
Restart=always
RestartSec=10
Nice=5
Environment=XDG_RUNTIME_DIR=${RUNTIME_DIR}
Environment=DOCKER_HOST=unix://${RUNTIME_DIR}/docker.sock
Environment=PIP_CACHE_DIR=${CACHE_ROOT}/pip
Environment=NPM_CONFIG_CACHE=${CACHE_ROOT}/npm
Environment=PLAYWRIGHT_BROWSERS_PATH=${CACHE_ROOT}/ms-playwright
NoNewPrivileges=yes
UMask=0077

[Install]
WantedBy=default.target
EOF
  install -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0600 "${tmp_unit}" "${unit_file}"
  rm -f -- "${tmp_unit}"
done

as_runner systemctl --user daemon-reload
for index in $(seq 1 "${RUNNER_COUNT}"); do
  service="actions-runner-${index}.service"
  as_runner systemctl --user enable "${service}"
  if as_runner systemctl --user is-active --quiet "${service}"; then
    as_runner systemctl --user restart "${service}"
  else
    as_runner systemctl --user start "${service}"
  fi
done

log "auditing the resulting isolation"
as_runner_groups="$(id -nG "${RUNNER_USER}")"
[[ " ${as_runner_groups} " != *" docker "* ]] || die "${RUNNER_USER} is still a member of the rootful docker group"
[[ " ${as_runner_groups} " != *" sudo "* ]] || die "${RUNNER_USER} is still a member of sudo"
docker_gid="$(getent group docker | cut -d: -f3 || true)"
[[ -z "${docker_gid}" || "$(id -g "${RUNNER_USER}")" != "${docker_gid}" ]] \
  || die "${RUNNER_USER} has the rootful docker group as its primary group"
for index in $(seq 1 "${RUNNER_COUNT}"); do
  as_runner systemctl --user is-active --quiet "actions-runner-${index}.service"
done
as_runner env DOCKER_HOST="${rootless_docker_host}" docker info --format '{{.DockerRootDir}}' \
  | grep -Fqx "${RUNNER_HOME}/.local/share/docker" \
  || die "the Docker root does not match the expected private root"

log "bootstrap complete: ${RUNNER_COUNT} runners and rootless Docker are active"
log "rootful Docker service/socket were not stopped, disabled, or reconfigured"
log "next: dispatch the LockLearn workflow and record the real run URLs and timings"
