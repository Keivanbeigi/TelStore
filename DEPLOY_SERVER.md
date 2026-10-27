# DEPLOY_SERVER.md — Deploy the TelStore Bot to a 24/7 Production Server

The TelStore bot is a resilient Python 3 program that polls the Telegram Bot API. To process payments and manage subscriptions around the clock, it must run on an always-on Linux VPS or dedicated server.

> Two deployment methods:
> - **[Method A] The one-command installer** (`bash scripts/deploy_server.sh`) — Recommended, automated systemd service setup.
> - **[Method B] Fully manual** — Useful for custom process supervisors (supervisor, Docker, systemd templates).

---

## System Requirements

- **Operating System:** Ubuntu 20.04+, Ubuntu 22.04+, Debian 11+, or any systemd-based Linux distribution.
- **Python Version:** Python 3.8 or higher.
- **Dependencies:** **Python standard library only.** No external pip packages (`urllib3`, `requests`, `pip`) are required.
- **Privileges:** Root or `sudo` access to register systemd service units.

---

## Method A — Automated Installer (Recommended)

### Step 1. Transfer the package to your server

From your local machine terminal:

```bash
scp -r telstore root@YOUR_SERVER_IP:~/
```

*(Or use SFTP clients such as WinSCP or FileZilla to upload the `telstore/` directory to your home folder).*

### Step 2. Connect via SSH

```bash
ssh root@YOUR_SERVER_IP
cd ~/telstore
```

### Step 3. Run the installer

```bash
bash scripts/deploy_server.sh
```

Answer the interactive prompts with your credentials:
1. **Telegram bot token** (from [@BotFather](https://t.me/BotFather))
2. **Owner chat_id** (from [@userinfobot](https://t.me/userinfobot))
3. **EVM wallet address** (BSC/ETH/Polygon — press Enter to skip manual crypto)
4. **NOWPayments API key** (press Enter to skip, or type `none` to disable)
5. **CoinGate Auth token** (press Enter to skip, or type `none` to disable)
6. **CoinGate KYC confirmation** (if token provided: confirm whether live payments are approved; answering `y` sets `COINGATE_ENABLED=1`, `n` sets `COINGATE_ENABLED=0`)

#### Installer Guarantees
- **Version Compatibility:** Validates all core release modules (`bot.py`, `storage.py`, `config.py`, etc.) before configuring.
- **Configuration Backup:** Creates a timestamped backup of any existing `.env` (`.env.bak_YYYYMMDD_HHMMSS`) with secure `600` permissions.
- **Fail-Closed Safety:** Halts immediately if backup creation fails.
- **Data Preservation:** Never overwrites or resets `subscribers.json`, `pending_payments.json`, or `manual_orders.json`.
- **Systemd Service:** Installs and enables `telstore-bot.service` to automatically launch on boot.

Expected completion output:
```text
✅ Bot service (telstore-bot) is RUNNING.
   Status : systemctl status telstore-bot
   Logs   : journalctl -u telstore-bot -f
```

### Step 4. Verify deployment

```bash
bash scripts/check_bot.sh
systemctl status telstore-bot
```

Open Telegram and send `/start` to your bot. As the owner, the **⚙️ Admin Menu** will appear.

---

## Method B — Non-Interactive Automated Installation

For scripted or headless CI/CD deployments where interactive prompts cannot be used:

```bash
cd ~/telstore
bash scripts/install_telstore.sh --install-dir /opt/telstore --service-name telstore-bot --create-service -y
```

- **`scripts/install_telstore.sh`** accepts command-line flags only (`--install-dir`, `--service-name`, `--create-service`, `--dry-run`, `-y`).
- Copies application files and registers the systemd unit without prompting for credentials.
- Pre-populate `/opt/telstore/.env` before launching the service.

---

## Method C — Manual Deployment

For containerized environments or existing supervisor configurations:

```bash
cd ~/telstore
cp scripts/.env.example .env
nano .env                          # Populate tokens, IDs, and keys
chmod 600 .env                     # Restrict file permissions to owner only
bash scripts/run_bot.sh            # Run in foreground
```

---

## Configuration Reference & Environment Isolation

All configuration values live in `.env` in the project root:

| Variable | Description | Production Requirement |
|----------|-------------|------------------------|
| `TELEGRAM_BOT_TOKEN` | Token provided by @BotFather | **Required** |
| `OWNER_CHAT_ID` | Owner numeric ID for admin privileges | **Required** |
| `CRYPTO_ADDRESS` | EVM address for manual crypto payments | Optional |
| `MANUAL_CHAIN` | Blockchain network for JSON-RPC verification (`BSC`, `Ethereum`, `Polygon`) | Optional (default: `BSC`) |
| `MANUAL_TOKEN_CONTRACT` | Specific ERC-20 token contract to require for manual payments | Optional (default: auto-detected USDT) |
| `NOWPAYMENTS_ENVIRONMENT` | Gateway environment: `production` or `sandbox` | Required if NOWPayments enabled |
| `NOWPAYMENTS_API_KEY` | Live API key from nowpayments.io | Required if NOWPayments enabled |
| `COINGATE_ENVIRONMENT` | Gateway environment: `production` or `sandbox` | Required if CoinGate enabled |
| `COINGATE_AUTH_TOKEN` | Live Auth token from coingate.com | Required if CoinGate enabled |
| `COINGATE_ENABLED` | Master switch for CoinGate button (`0` or `1`); keep `0` until KYC approved | Optional (default: `0`) |
| `PRICE_USD` | Default product pricing in USD | Optional (default: 5) |
| `PREMIUM_DAYS` | Default subscription duration in days | Optional (default: 30) |
| `CHANNEL_ID` | Telegram VIP channel ID (`-100...`) | Optional (for channel access) |
| `CHANNEL_LINK` | Invite link for VIP channel | Optional |
| `SUPPORT_URL` | Support handle or URL displayed in menu | Optional |
| `WEBSITE_URL` | Official website URL displayed in menu | Optional |

> **Security Rule:** TelStore strictly isolates sandbox and production credentials. The application refuses to transmit sandbox credentials to live endpoints or vice versa (`GatewayConfigurationError`).

---

## Day-to-Day Service Management

| Task | Command |
|------|---------|
| Check service status | `systemctl status telstore-bot` |
| View live logs | `journalctl -u telstore-bot -f` |
| View last 50 log lines | `journalctl -u telstore-bot -n 50 --no-pager` |
| Restart bot (after .env update) | `systemctl restart telstore-bot` |
| Stop bot temporarily | `systemctl stop telstore-bot` |
| Enable autostart on boot | `systemctl enable telstore-bot` |
| Disable autostart | `systemctl disable telstore-bot` |

---

## Upgrades, Backups, and Rollback Procedures

### Upgrading an Existing Installation
When applying code updates:
1. Copy updated scripts into `telstore/scripts/`.
2. Run `bash scripts/deploy_server.sh`.
3. The script will detect existing settings and allow you to keep them by pressing Enter.
4. Existing customer subscriptions (`subscribers.json`) and orders (`pending_payments.json`) are preserved automatically.

### Database Backup & Restore Principles
- **Critical Data Files:**
  - `scripts/subscribers.json` — All subscriber access expiration dates and processed transaction IDs (`processed_payments`).
  - `scripts/pending_payments.json` — In-flight payment sessions.
  - `scripts/manual_orders.json` — Manual card/wallet payment tickets.
  - `.env` — Secret credentials.
- **Backup Command:**
  ```bash
  tar -czf telstore_backup_$(date +%Y%m%d_%H%M%S).tar.gz telstore/
  ```
- **Delta Merge Rule:** During rollbacks or downgrades, **never blindly overwrite `subscribers.json` with an older snapshot**. New customers who paid during the run window must be merged (by appending newer entries and retaining the latest `expiry` timestamp) to prevent subscriber loss.

---

## Safe Uninstallation

To safely remove TelStore from your server:

```bash
# 1. Preview changes (Dry-Run):
bash scripts/uninstall_server.sh --dry-run

# 2. Execute safe uninstallation:
bash scripts/uninstall_server.sh
```

### Uninstaller Guarantees:
- **Mandatory Backup:** Creates a full compressed snapshot (`/tmp/telstore_pre_uninstall_*.tar.gz`) before making any changes. Halts immediately if backup fails.
- **Service Decommissioning:** Safely stops and disables `telstore-bot` systemd service and deletes `/etc/systemd/system/telstore-bot.service`.
- **Absolute Data Protection:** Removes application binaries and caches while **strictly preserving** `subscribers.json`, `pending_payments.json`, `manual_orders.json`, `.env`, and all `.bak_*` backups.

---

## Troubleshooting

| Problem | Root Cause | Solution |
|---------|------------|----------|
| `python3: command not found` | Python not installed | Run `apt-get update && apt-get install -y python3`. |
| `Python 3.8+ is required` | Outdated Python version | Upgrade system Python to 3.8 or newer. |
| Bot not responding to `/start` | Invalid token or network blockage | Verify token in `.env`; run `bash scripts/check_bot.sh`. |
| `SingleInstanceLock: already running` | Stale lock or concurrent process | Verify single instance: `ps aux \| grep bot.py`. If bot crashed, remove `rm -f scripts/bot.lock`. |
| Gateway buttons missing in menu | API credentials empty or invalid | Enter credentials in `.env` and restart: `systemctl restart telstore-bot`. |
| `GatewayConfigurationError` | Environment mismatch | Verify `NOWPAYMENTS_ENVIRONMENT=production` matches production API keys. |
