#!/usr/bin/env bash
# Deploy the CURRENT working bot (from WSL) to the remote server.
# Copies code + real .env, installs as systemd service (24/7).
set -euo pipefail

SERVER="root@145.63.135.239"
SRC_WSL="/home/keivan/cqb_test/scripts"
REMOTE="/opt/crypto-quest-bot"

echo "=== 1. Build deploy bundle from WSL (working bot) ==="
# create a staging dir from the working WSL scripts
STAGE=$(mktemp -d)
mkdir -p "$STAGE/crypto-quest-bot/scripts"
cp "$SRC_WSL"/bot.py "$SRC_WSL"/config.py "$SRC_WSL"/lang.py \
   "$SRC_WSL"/admin.py "$SRC_WSL"/channel_access.py \
   "$SRC_WSL"/nowpayments.py "$SRC_WSL"/coingate.py \
   "$SRC_WSL"/broadcast.py "$SRC_WSL"/run_bot.sh \
   "$SRC_WSL"/deploy_server.sh "$SRC_WSL"/check_bot.sh \
   "$SRC_WSL"/requirements.txt "$SRC_WSL"/.env.example \
   "$STAGE/crypto-quest-bot/scripts/"
echo "    code copied"

echo "==> 2. Copy real .env (working token/wallet/API) =="
cp /home/keivan/cqb_test/.env "$STAGE/crypto-quest-bot/.env" 2>/dev/null \
  || cp /home/keivan/cqb_test/scripts/.env "$STAGE/crypto-quest-bot/.env"
echo "    .env copied"

echo "==> 3. tar bundle =="
cd "$STAGE" && tar czf /tmp/cqb-deploy.tar.gz crypto-quest-bot
echo "    bundle: $(ls -la /tmp/cqb-deploy.tar.gz | awk '{print $5}') bytes"
echo "$STAGE"