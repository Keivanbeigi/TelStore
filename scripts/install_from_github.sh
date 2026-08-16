#!/usr/bin/env bash
# ============================================================
#  TelStore Telegram Bot — install from PRIVATE GitHub
#  ------------------------------------------------------------
#  Downloads the bot source from YOUR PRIVATE GitHub repo, then
#  runs the interactive installer (asks the owner for their own
#  Telegram token, wallet, NOWPayments key) and sets up a 24/7
#  systemd service.
#
#  REQUIREMENTS:
#    - A GitHub Personal Access Token (PAT) that can read the repo.
#      Create one: GitHub → Settings → Developer settings →
#      Personal access tokens → Fine-grained → repo (read) scope.
#
#  USAGE:
#    1) Put this script on your server (anywhere).
#    2) Set your token + repo:
#         export GITHUB_TOKEN="ghp_..."      # your PAT (read-only, repo scope)
#         export REPO_URL="https://github.com/YOU/TelStore.git"
#    3) Run it:  bash install_from_github.sh
#    4) Answer the prompts with YOUR OWN values.
#
#  It clones the private repo, asks for your credentials, writes
#  .env, and installs the systemd service. The token is only used
#  to clone once and is NOT stored in .env or on disk.
# ============================================================
set -e

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
say(){ echo -e "${GREEN}[telstore]${NC} $*"; }
err(){ echo -e "${RED}[error]${NC} $*"; exit 1; }

# --- 0. required inputs ----------------------------------------------------
if [ -z "${GITHUB_TOKEN:-}" ]; then
  err "GITHUB_TOKEN is not set. Export it first, e.g.  export GITHUB_TOKEN=ghp_..."
fi
if [ -z "${REPO_URL:-}" ]; then
  echo -e "${YELLOW}[error]${NC} REPO_URL is not set."
  echo -e "${YELLOW}       Ask the seller for the installation URL they emailed you, then run:${NC}"
  echo -e "${YELLOW}         export REPO_URL=\"https://github.com/<seller-org>/TelStore.git\"${NC}"
  exit 1
else
  # strip trailing .git if present to keep URLs consistent
  REPO_URL="${REPO_URL%.git}.git"
fi
if ! command -v git >/dev/null 2>&1; then
  err "git is required. Install it: apt-get install -y git"
fi

# --- 1. clone the private repo (using token auth) --------------------------
# Token goes in the URL for this one clone only; we never store it.
# Build the authenticated URL from the two exported vars, so no personal or
# fixed account name is hard-coded into this file.
AUTH_URL="https://x-access-token:${GITHUB_TOKEN}@${REPO_URL#https://}"
DEST="/opt/telstore"

say "Cloning private repo: ${REPO_URL}"
if [ -d "$DEST" ]; then
  say "Removing old copy at $DEST"
  rm -rf "$DEST"
fi
git clone --depth 1 "$AUTH_URL" "$DEST"
rm -rf "$DEST/.git"   # drop git history (keeps token out of logs/reflog)
say "Cloned to $DEST"

# --- 2. run the interactive installer -----------------------------------
# The cloned repo contains scripts/deploy_server.sh which asks for the
# buyer's token/wallet/API and sets up the systemd service.
cd "$DEST"
bash scripts/deploy_server.sh