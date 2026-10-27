# INSTALL.md — Install the TelStore Bot (Quick Start)

This is the shortest path to a running bot on an Ubuntu/Debian VPS or WSL.
For the full server-deployment walkthrough (uploads, systemd service, day-to-day
management, backup/restore, and uninstallation), see **DEPLOY_SERVER.md**.

## What you need before you start

| Requirement | Where to get it | Notes |
|-------------|-----------------|-------|
| Python 3.8+ | System package (`apt-get install -y python3`) | **Standard library only** — no pip packages needed |
| A server (Ubuntu/Debian VPS) or WSL | Any hosting / VPS provider | 24/7 always-on host recommended |
| Telegram bot token | [@BotFather](https://t.me/BotFather) → `/newbot` | Required |
| Your Telegram chat_id | [@userinfobot](https://t.me/userinfobot) | Required for Admin Menu and owner alerts |
| An EVM wallet `0x...` | e.g. MetaMask / TrustWallet | Optional — for direct crypto payments |
| NOWPayments API key | [nowpayments.io](https://nowpayments.io) → Settings → API Keys | Optional — automatic crypto checkout |
| CoinGate Auth token | [coingate.com](https://coingate.com) → Settings → API | Optional — hosted crypto invoice checkout |

---

## The one-command installer (recommended)

On your server, inside the `telstore/` directory:

```bash
cd telstore
bash scripts/deploy_server.sh
```

The installer verifies your Python version and asks for your configuration values:

1. **Telegram bot token** — paste token from @BotFather
2. **Owner chat_id** — paste your user ID from @userinfobot
3. **EVM wallet** — enter `0x...` address (or press Enter to skip manual crypto)
4. **NOWPayments API key** — enter live API key (or type `none` / press Enter to skip)
5. **CoinGate Auth token** — enter live Auth token (or type `none` / press Enter to skip)
6. **CoinGate KYC confirmation** — if a CoinGate token was entered, confirm if business KYC is approved. Answering `y` enables checkout (`COINGATE_ENABLED=1`); answering `n` leaves the button hidden (`COINGATE_ENABLED=0`) to avoid 422 errors.

### Safe Upgrade Guarantees
- If updating an existing installation, the installer **preserves your existing values** as defaults. Press Enter to retain them.
- Creates an **atomic, timestamped backup** of your existing `.env` file (`.env.bak_YYYYMMDD_HHMMSS`) before writing changes.
- **Fail-closed**: If backup creation fails, the script halts immediately without altering files.
- **Data safety**: Your subscriber records (`subscribers.json`) and pending orders (`pending_payments.json`) are **never modified or overwritten**.

When it completes, you will see `✅ Bot service (telstore-bot) is RUNNING.` The bot runs as a **systemd service** and restarts automatically on boot.

---

## CoinGate KYC Requirement (`COINGATE_ENABLED`)

CoinGate strictly refuses unpaid and new customer orders with HTTP `422 Business is not verified` until your CoinGate business account KYC verification has been reviewed and approved.

- By default, `COINGATE_ENABLED=0` keeps the CoinGate button hidden so buyers never hit 422 errors.
- Once your CoinGate account is approved for live payments, set `COINGATE_ENABLED=1` in your `.env` (or answer `y` during `deploy_server.sh`) and restart the bot (`systemctl restart telstore-bot`).

---

## Real File Delivery for Digital Products (`scripts/file_delivery.py`)

TelStore delivers **real files** to buyers:
- When adding a **digital** product in the Admin Menu wizard (Step 7/8), the bot prompts you to upload the file itself (PDF, video, audio, photo, or document).
- When a customer purchases a digital product, the bot delivers the real file directly into their Telegram chat using the Telegram Bot API (`sendDocument`, `sendVideo`, `sendAudio`, `sendPhoto`). If sending the file fails, it automatically falls back to sending the delivery text or link so the buyer is never left empty-handed.
- For **channel** products (VIP membership), the wizard skips the file upload step entirely and delivers a single-use channel invite link instead.
- You can attach or replace a digital product's file at any time using the `/set_file <product_id>` admin command.

---

## Server Scripts Overview

TelStore includes modular shell scripts to handle server operations:

- **`scripts/deploy_server.sh`** — The **interactive** installer (recommended for buyers). Interactively prompts for token, owner chat ID, wallet, NOWPayments key, CoinGate token, and KYC confirmation; creates a timestamped `.env` backup and registers the systemd service.
- **`scripts/install_telstore.sh`** — The **non-interactive** installer for headless or scripted deployments (accepts `--install-dir`, `--service-name`, `--create-service`, `--dry-run`, `-y`). Sets up directories and systemd units without prompting for credentials.
- **`scripts/uninstall_server.sh`** — The safe uninstaller. Takes a mandatory full pre-uninstallation tarball archive (`/tmp/telstore_pre_uninstall_*.tar.gz`), stops and disables `telstore-bot`, removes code, and **strictly preserves** `.env` and customer database files by default.
- **`scripts/check_bot.sh`** — Health diagnostic and configuration audit tool. Tests Python environment, imports, gateway credentials, network connectivity, and systemd service state.

---

## Verify the installation

```bash
bash scripts/check_bot.sh        # built-in health diagnostic
systemctl status telstore-bot    # systemd service status
```

Then open Telegram and send `/start` to your bot. As the owner, you will see the **⚙️ Admin Menu** button.

---

## Manual (no installer)

If you prefer running the bot manually or in a container:

```bash
cd telstore
cp scripts/.env.example .env     # edit with YOUR token, owner id, wallet, keys
chmod 600 .env                   # protect your secrets
bash scripts/run_bot.sh          # runs in foreground (closing terminal stops bot)
```

---

## Safe uninstallation

If you ever need to decommission or remove the bot from your server:

```bash
# Preview actions without modifying anything (dry-run):
bash scripts/uninstall_server.sh --dry-run

# Run safe uninstaller:
bash scripts/uninstall_server.sh
```

The uninstaller:
1. Creates a full pre-uninstallation backup archive (`/tmp/telstore_pre_uninstall_*.tar.gz`).
2. Stops and disables the `telstore-bot` systemd service.
3. Cleans up application code files.
4. **Strictly preserves** all customer subscriptions (`subscribers.json`), orders (`pending_payments.json`), and configuration (`.env`).
