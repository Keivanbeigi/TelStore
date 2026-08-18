# INSTALL.md — Install the TelStore Bot (quick start)

This is the shortest path to a running bot on a Ubuntu/Debian VPS or WSL.
For the full server-deployment walkthrough (uploads, systemd service, day-to-day
management), see **DEPLOY_SERVER.md**.

## What you need before you start

| Requirement | Where to get it |
|-------------|-----------------|
| A server (Ubuntu/Debian VPS) or WSL on your PC | Any hosting / WSL (the Ubuntu app) |
| Telegram bot token | [@BotFather](https://t.me/BotFather) → `/newbot` |
| Your Telegram chat_id | [@userinfobot](https://t.me/userinfobot) |
| An EVM wallet `0x...` *(optional)* | e.g. MetaMask |
| NOWPayments API key *(optional)* | [nowpayments.io](https://nowpayments.io) → Settings → API Keys |
| CoinGate API token *(optional)* | [coingate.com](https://coingate.com) → Settings → API |

## The one-command installer (recommended)

On your server, in the `telstore/` folder:

```bash
cd telstore
bash scripts/deploy_server.sh
```

The installer asks you for your **own** values:

1. Telegram bot token
2. Your Telegram chat_id
3. Your EVM wallet (optional — Enter to skip)
4. NOWPayments API key (optional — Enter to skip)

When it finishes you see `✅ Bot service is RUNNING.` The bot is installed as a
**systemd service** named `telstore-bot` and restarts automatically on boot.

## Verify

```bash
bash scripts/check_bot.sh        # all-health check
```

Then open Telegram and send `/start` to your bot.

## Manual (no installer)

```bash
cd telstore
cp scripts/.env.example .env     # edit with YOUR token, owner id, wallet, keys
bash scripts/run_bot.sh          # runs in the foreground (closing = bot stops)
```

For a 24/7 bot, run the installer above instead so it survives reboots.