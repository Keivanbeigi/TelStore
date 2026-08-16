#!/usr/bin/env bash
# Build a clean deploy bundle from the working WSL bot + real .env
set -e
STAGE=$(mktemp -d)
ROOT="$STAGE/crypto-quest-bot"
mkdir -p "$ROOT/scripts"

# 1. code from the working WSL bot (has all fixes)
cp /home/keivan/cqb_test/scripts/{bot.py,config.py,lang.py,admin.py,channel_access.py,nowpayments.py,coingate.py,broadcast.py,run_bot.sh,deploy_server.sh,check_bot.sh,requirements.txt,.env.example} "$ROOT/scripts/"

# 2. real .env from the working bot (your token/wallet/API)
cp /home/keivan/cqb_test/scripts/.env "$ROOT/.env"

echo "bundle at $ROOT:"
ls "$ROOT" "$ROOT/scripts"
echo "---"
echo "real .env has:"
grep -oE "^[A-Z_]+=" "$ROOT/.env"
echo "$ROOT"