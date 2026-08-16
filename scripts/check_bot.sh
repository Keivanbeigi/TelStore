#!/usr/bin/env bash
# ============================================================
#  TelStore Telegram Bot — health check / self-test
#  ------------------------------------------------------------
#  Runs a full diagnostic on a server (or WSL) where the bot
#  is deployed. Portable: works on any Ubuntu/Debian with
#  Python 3.8+ and a completed deploy_server.sh install.
#
#  USAGE:
#     cd telstore && bash scripts/check_bot.sh
#
#  Checks (each prints PASS/FAIL):
#     1. Python 3 available (3.8+)
#     2. All modules import & compile (bot, config, lang, ...)
#     3. .env exists and TELEGRAM_BOT_TOKEN is set
#     4. Telegram token is VALID (calls getMe via Bot API)
#     5. NOWPayments configured -> live API ping works
#     6. CoinGate configured (optional) -> token present
#     7. Data files writable (subscribers, pending)
#     8. systemd service state (if systemd is present)
#
#  Exit code: 0 = all good, 1 = something failed.
# ============================================================
set -u

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS(){ echo -e "${GREEN}  PASS${NC}  $*"; }
FAIL(){ echo -e "${RED}  FAIL${NC}  $*"; FAILED=1; }
NOTE(){ echo -e "${YELLOW}  NOTE${NC}  $*"; }
FAILED=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
echo "— TelStore bot health check —"
echo "  root: $ROOT"
echo ""

# --- 1. python3 ------------------------------------------------------------
echo "[1/8] Python"
if command -v python3 >/dev/null 2>&1; then
  PY="python3"
  PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
elif command -v python >/dev/null 2>&1; then
  PY="python"
  PYVER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
else
  FAIL "python3 / python not found — run deploy_server.sh first"
  PY=""
  PYVER=""
fi
if [ -n "${PY:-}" ] && [ -n "${PYVER:-}" ]; then
  MAJOR="${PYVER%%.*}"; MINOR="${PYVER#*.}"
  if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
    PASS "python ($PY) $PYVER (>= 3.8)"
  else
    FAIL "python $PYVER is too old (need 3.8+)"
  fi
fi
echo ""

# --- 2. modules compile ----------------------------------------------------
echo "[2/8] Modules import"
cd "$SCRIPT_DIR"
for mod in config lang admin channel_access nowpayments bot; do
  if "$PY" -c "import $mod" 2>/dev/null; then
    PASS "import $mod"
  else
    FAIL "import $mod -> $("$PY" -c "import $mod" 2>&1 | tail -1)"
  fi
done
echo ""

# --- 3. .env / token set ---------------------------------------------------
echo "[3/8] Configuration"
if [ -f "$ROOT/.env" ]; then
  PASS ".env exists"
elif [ -f "$SCRIPT_DIR/.env" ]; then
  PASS ".env exists (scripts/)"
else
  FAIL ".env missing — copy from scripts/.env.example and fill it in"
fi
ENV_FILE="$ROOT/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="$SCRIPT_DIR/.env"
TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]' | sed 's/^"//; s/"$//')
if [ -n "$TOKEN" ] && [ "$TOKEN" != "your_bot_token_here" ]; then
  PASS "TELEGRAM_BOT_TOKEN is set (${TOKEN:0:6}...)"
else
  FAIL "TELEGRAM_BOT_TOKEN empty/placeholder — edit $ENV_FILE"
fi
OWNER=$(grep -E '^OWNER_CHAT_ID=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')
if [ -n "$OWNER" ]; then
  PASS "OWNER_CHAT_ID is set"
else
  NOTE "OWNER_CHAT_ID empty (owner admin commands disabled — optional)"
fi
echo ""

# --- 4. Telegram getMe (live) ----------------------------------------------
echo "[4/8] Telegram API (live)"
if [ -n "${TOKEN:-}" ] && [ "$TOKEN" != "your_bot_token_here" ]; then
  GME=$("$PY" - "$TOKEN" <<'PY'
import json, sys, urllib.request
tok = sys.argv[1]
try:
    with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=15) as r:
        d = json.loads(r.read())
    ok = d.get("ok")
    name = (d.get("result") or {}).get("username", "")
    print(f"{ok}|{name}")
except Exception as e:
    print(f"False|{e}")
PY
)
  if [ "${GME%%|*}" = "True" ]; then
    PASS "token valid — bot @${GME#*|}"
  else
    FAIL "getMe failed: ${GME#*|}"
  fi
fi
echo ""

# --- 5. NOWPayments (live) -------------------------------------------------
echo "[5/8] NOWPayments"
NP_KEY=$(grep -E '^NOWPAYMENTS_API_KEY=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')
if [ -z "$NP_KEY" ]; then
  NOTE "NOWPAYMENTS_API_KEY empty — the NOWPayments button is hidden (optional)"
else
  NPT=$("$PY" - "$NP_KEY" <<'PY'
import json, sys, urllib.request
key = sys.argv[1]
try:
    # Cloudflare in front of api.nowpayments.io blocks urllib's default
    # User-Agent (403 error 1010) - send a browser UA like nowpayments.py does.
    req = urllib.request.Request(
        "https://api.nowpayments.io/v1/status",
        headers={"x-api-key": key, "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    ok = d.get("message") == "OK" or d.get("statusAvailable") is True
    print(f"{ok}|{d.get('message','ok')}")
except Exception as e:
    print(f"False|{e}")
PY
)
  if [ "${NPT%%|*}" = "True" ]; then
    PASS "NOWPayments API reachable with key"
  else
    FAIL "NOWPayments API check failed: ${NPT#*|}"
  fi
fi
echo ""

# --- 6. CoinGate (optional) ------------------------------------------------
echo "[6/8] CoinGate"
CG_TOKEN=$(grep -E '^COINGATE_AUTH_TOKEN=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')
if [ -z "$CG_TOKEN" ]; then
  NOTE "COINGATE_AUTH_TOKEN empty — CoinGate button hidden (optional)"
else
  PASS "COINGATE_AUTH_TOKEN is set"
fi
echo ""

# --- 7. data files writable ------------------------------------------------
echo "[7/8] Data files"
for f in subscribers.json pending_payments.json menu_config.json products.json; do
  P="$ROOT/scripts/$f"
  if [ -e "$P" ]; then
    if [ -w "$P" ]; then PASS "$f writable"; else FAIL "$f NOT writable"; fi
  else
    if [ -w "$ROOT/scripts" ]; then PASS "$f missing but dir writable (will be created)"; else FAIL "$f missing & scripts/ NOT writable"; fi
  fi
done
echo ""

# --- 8. systemd ------------------------------------------------------------
echo "[8/8] Service"
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet telstore 2>/dev/null; then
    PASS "telstore service RUNNING"
    NOTE "  journalctl -u telstore -n 50 --no-pager"
  else
    FAIL "telstore service NOT running (systemctl status telstore)"
  fi
else
  NOTE "systemd not present — run bot with: bash scripts/run_bot.sh (or nohup)"
fi
echo ""

# --- summary ---------------------------------------------------------------
if [ "$FAILED" = "1" ]; then
  echo "❌ RESULT: some checks FAILED — fix the FAIL lines above, then re-run."
  exit 1
fi
echo "✅ RESULT: ALL CHECKS PASSED — the bot is healthy."
exit 0