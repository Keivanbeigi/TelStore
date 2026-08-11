#!/usr/bin/env bash
# ============================================================
#  Crypto Quest Telegram Bot — one-shot server installer
#  ------------------------------------------------------------
#  Runs the bot as a 24/7 background service (systemd) so it
#  stays online even after you close the SSH session / reboot.
#
#  Tested on Ubuntu / Debian (any Python 3.8+).
#
#  USAGE:
#    1) Copy the whole crypto-quest-bot/ folder to your server
#       (scp -r crypto-quest-bot user@server:~/)
#    2) cd crypto-quest-bot && bash scripts/deploy_server.sh
#    3) Follow the prompts (bot token, wallet, owner id, ...)
#
#  The script:
#     - checks/installs python3
#     - creates .env from .env.example (keeps an existing .env)
#     - installs a systemd service named 'crypto-quest-bot'
#     - starts it now and enables it to start on boot
#
#  Useful commands:
#     systemctl status crypto-quest-bot   # is it running?
#     journalctl -u crypto-quest-bot -f   # live logs
#     systemctl restart crypto-quest-bot  # restart the bot
# ============================================================
set -e

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
say(){ echo -e "${GREEN}[crypto-quest]${NC} $*"; }
warn(){ echo -e "${YELLOW}[warn]${NC} $*"; }
err(){ echo -e "${RED}[error]${NC} $*"; exit 1; }

# --- 1. locate project root (folder that contains scripts/) ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
if [ ! -f "$SCRIPT_DIR/bot.py" ]; then
  warn "bot.py not found next to this script; expecting crypto-quest-bot/scripts/bot.py"
fi
say "Project root: $ROOT"

# --- 2. python3 ------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PY="python3"; say "python3 found: $($PY --version 2>&1)"
else
  warn "python3 not found — installing..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y python3
  else
    err "No apt-get. Please install Python 3.8+ manually, then re-run."
  fi
fi

# --- 3. .env ---------------------------------------------------------------
ENV_FILE="$ROOT/.env"
ENV_EXAMPLE="$ROOT/scripts/.env.example"
if [ -f "$ENV_FILE" ]; then
  say ".env already exists — keeping it."
else
  if [ ! -f "$ENV_EXAMPLE" ]; then
    err ".env.example not found at $ENV_EXAMPLE"
  fi
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  say "Created .env from .env.example — EDIT IT NOW with your values:"
  say "   nano $ENV_FILE"
  read -r -p "Press Enter after you have filled in .env... " _
fi

# --- 4. systemd service ----------------------------------------------------
SERVICE_NAME="crypto-quest-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
RUN_BIN="$SCRIPT_DIR/run_bot.sh"

# create a tiny run script (so systemd uses the right python)
cat > "$RUN_BIN" <<EOF
#!/usr/bin/env bash
cd "$ROOT/scripts"
exec $PY -u bot.py
EOF
chmod +x "$RUN_BIN"

cat > /tmp/crypto-quest-bot.service <<EOF
[Unit]
Description=Crypto Quest Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT/scripts
ExecStart=$RUN_BIN
Restart=always
RestartSec=5
EnvironmentFile=$ENV_FILE

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/crypto-quest-bot.service "$SERVICE_FILE"
rm -f /tmp/crypto-quest-bot.service

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" >/dev/null 2>&1
sudo systemctl restart "$SERVICE_NAME"

# --- 5. report -------------------------------------------------------------
sleep 3
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  say "✅ Bot service is RUNNING."
  say "   Status : systemctl status $SERVICE_NAME"
  say "   Logs   : journalctl -u $SERVICE_NAME -f"
  say "   Restart: systemctl restart $SERVICE_NAME"
  say "The bot will auto-start on every boot."
else
  err "Service did not start. See: journalctl -u $SERVICE_NAME -n 50"
fi