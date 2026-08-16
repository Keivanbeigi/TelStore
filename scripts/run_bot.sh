#!/usr/bin/env bash
# Run the TelStore bot with python3 (used by deploy_server.sh / systemd).
cd "$(dirname "$0")"
exec python3 -u bot.py