#!/usr/bin/env bash
# Run as the pumplab user (ssh pumplab@<droplet-ip>), in two passes:
#
#   Pass 1:  bash bootstrap_user.sh keys
#            -> creates a GitHub deploy key and prints it. Add it to the repo
#               (Settings -> Deploy keys -> Add, tick "Allow write access").
#   Pass 2:  bash bootstrap_user.sh install
#            -> installs uv + Claude Code, clones the repo, runs tests,
#               installs the collector + rollup services (not started yet).
set -euo pipefail

REPO_SSH="git@github.com:itskaysyoga-gif/pumpfun.git"
KEY="$HOME/.ssh/github_pumpfun"

if [[ "$(id -un)" != "pumplab" ]]; then echo "Run as pumplab"; exit 1; fi

case "${1:-}" in
keys)
  if [[ ! -f "$KEY" ]]; then
    ssh-keygen -t ed25519 -N "" -C "pumplab-droplet deploy key" -f "$KEY"
  fi
  cat > "$HOME/.ssh/config" <<EOF
Host github.com
  IdentityFile $KEY
  IdentitiesOnly yes
EOF
  chmod 600 "$HOME/.ssh/config"
  ssh-keyscan -t ed25519 github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null
  echo
  echo "=== Copy this whole line into GitHub -> pumpfun repo -> Settings -> Deploy keys -> Add deploy key ==="
  echo "=== Title: pumplab-droplet.  Tick 'Allow write access'. ==="
  cat "$KEY.pub"
  ;;
install)
  gh_check="$(ssh -T git@github.com 2>&1 || true)"   # ssh -T always exits 1 on GitHub
  if ! grep -q "successfully authenticated" <<<"$gh_check"; then
    echo "GitHub deploy key not working yet. Add it (pass 1) and retry."
    echo "$gh_check"; exit 1
  fi

  command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
  command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
  # shellcheck disable=SC2016  # literal $HOME/$PATH wanted in .bashrc
  grep -q '.local/bin' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

  [[ -d "$HOME/pumpfun" ]] || git clone "$REPO_SSH" "$HOME/pumpfun"
  cd "$HOME/pumpfun"
  git config user.name "Hussein Slim"
  git config user.email "hsleem@gmail.com"
  [[ -f .env ]] || { cp .env.example .env; chmod 600 .env; }
  uv sync
  uv run pytest -q

  mkdir -p "$HOME/.config/systemd/user"
  cp deploy/pumplab-collector.service deploy/pumplab-rollup.service deploy/pumplab-rollup.timer \
     "$HOME/.config/systemd/user/"
  XDG_RUNTIME_DIR="/run/user/$(id -u)"; export XDG_RUNTIME_DIR
  systemctl --user daemon-reload
  echo
  echo "Installed. claude: $(claude --version 2>/dev/null || echo 'open a new shell')"
  echo "Collector is NOT started yet; Claude starts it after the probe passes."
  ;;
*)
  echo "usage: bash bootstrap_user.sh keys|install"; exit 1;;
esac
