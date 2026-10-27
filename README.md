# TelStore Bot v1.1 — Telegram Payment & VIP Subscription Bot

A complete, production-hardened Telegram bot for selling digital products and VIP channel
access with automated crypto payments (NOWPayments + CoinGate) and manual wallet verification.
It runs 24/7 on your Linux server, survives restarts, and is fully configurable from Telegram.

## Documentation Index

Everything you need ships directly in this package:

- **`INSTALL.md`** — 2-minute quick-start installation guide
- **`DEPLOY_SERVER.md`** — Comprehensive 24/7 server deployment, upgrades, backup, and uninstallation
- **`BUYER_GUIDE.md`** — Welcome walkthrough, first 15 minutes, and admin administration
- **`ARCHITECTURE.md`** — System architecture, storage engine, and security invariants
- **`FOR_SELLER.md`** — Seller's distribution, build verification, and clean package checklist
- **`README.fa.md`** — Persian documentation for Persian-speaking administrators
- This **`README.md`** — Complete technical reference index and operational manual

---

## 1. What You Received

You received the **complete, self-hosted bot software**. You install it on your own server, connect your Telegram bot token, your crypto payout wallet, and your payment gateway credentials.

- **Zero Tracking:** The bot never phones home, uses third-party analytics, or communicates with any servers other than Telegram and your configured payment gateways.
- **Direct Payouts:** 100% of customer payments go directly to your crypto wallet or gateway accounts.
- **Pure Python:** Built exclusively on Python 3.8+ standard library. Zero external pip dependencies required.

---

## 2. Prerequisites

Prepare these values before deploying:

| Requirement | Where to get it | Notes |
|-------------|-----------------|-------|
| **Linux Server / VPS** | Any Ubuntu / Debian VPS | Python 3.8+ installed; runs 24/7 as systemd service |
| **Telegram Bot Token** | [@BotFather](https://t.me/BotFather) → `/newbot` | **Required** for bot polling and messaging |
| **Telegram Chat ID** | [@userinfobot](https://t.me/userinfobot) | **Required** to grant admin privileges and receive alerts |
| **Crypto Wallet Address** | Any EVM address (`0x...` BSC/ETH/Polygon) | Optional — enables manual crypto payment flow |
| **NOWPayments API Key** | [nowpayments.io](https://nowpayments.io) | Optional — enables automatic crypto checkout |
| **CoinGate Auth Token** | [coingate.com](https://coingate.com) | Optional — enables hosted web checkout (requires KYC; button hidden until `COINGATE_ENABLED=1`) |

---

## 3. Installation Options

### Method A: Interactive Installer (Recommended for Buyers)

The interactive installer guides you step-by-step through configuration, validates entries, sets secure permissions (`chmod 600 .env`), and sets up the systemd service:

```bash
cd telstore
bash scripts/deploy_server.sh
```

The installer prompts for your configuration values:
1. **Telegram bot token**
2. **Admin chat_id**
3. **Crypto wallet address** (optional, press Enter to skip)
4. **NOWPayments API key** (optional, press Enter to skip)
5. **CoinGate Auth token** (optional, press Enter to skip)
6. **CoinGate KYC verification status** (y/n — sets `COINGATE_ENABLED=1` only if approved)

### Method B: Non-Interactive / Unattended Installer

For automated or scripted VPS deployments, use `install_telstore.sh` with command-line flags:

```bash
bash scripts/install_telstore.sh --install-dir /opt/telstore --service-name telstore-bot --create-service -y
```

Flags supported:
- `--install-dir <path>`: Target installation directory (default: current directory).
- `--service-name <name>`: Systemd service name (default: `telstore-bot`).
- `--create-service`: Installs and enables the systemd service unit.
- `--dry-run`: Previews actions without modifying the filesystem or systemd.
- `-y`, `--yes`: Non-interactive mode; auto-approves all prompts.

### Safe Upgrade & Data Guarantees
- **Existing Settings Preserved:** If re-running on an existing server, installers detect current settings and use them as defaults.
- **Fail-Closed Backup:** Generates an atomic backup of `.env` (`.env.bak_YYYYMMDD_HHMMSS`) before writing updates. Halts immediately if backup fails.
- **Zero Data Loss:** Customer subscriptions (`subscribers.json`) and orders (`pending_payments.json`) are never modified or reset by the installer.
- **Systemd Autostart:** Automatically installs, enables, and starts the `telstore-bot` systemd service.

---

## 4. Verification & Diagnostics

Run the integrated health check:

```bash
bash scripts/check_bot.sh
systemctl status telstore-bot
```

Open Telegram and send `/start` to your bot. As owner, you will see the **⚙️ Admin Menu** button.

---

## 5. Day-to-Day Service Management

```bash
systemctl status telstore-bot        # Check service status
journalctl -u telstore-bot -f        # View live logs (Ctrl+C to exit)
systemctl restart telstore-bot       # Restart service after editing .env
systemctl stop telstore-bot          # Stop service
```

---

## 6. Architecture & Data Safety Highlights

Version 1.1 includes enterprise-grade resilience and data safety enhancements:

1. **Atomic Storage Engine (`scripts/storage.py`):**
   - Eliminates data truncation or corruption during server reboots or crashes via atomic write-and-replace (`mkstemp`, `fsync`, `os.replace`).
   - Strict corruption detection: raises `DatabaseCorruptedError` instead of wiping databases with empty defaults.
2. **Crash-Safe Payment Idempotency:**
   - Every confirmed payment is durably recorded in `processed_payments` inside `subscribers.json` in the same atomic transaction as the subscription renewal.
   - Prevents double-crediting if a network timeout or crash occurs during order clearance.
3. **Process Concurrency Lock (`SingleInstanceLock`):**
   - Enforces single-instance execution via OS-level file locking (`msvcrt` on Windows, `fcntl` on Linux). Prevents dual-bot polling collisions.
4. **Strict Gateway Isolation:**
   - Enforces separate sandbox and production configurations (`NOWPAYMENTS_ENVIRONMENT`, `COINGATE_ENVIRONMENT`). Prevents credential cross-contamination.
5. **Real File Delivery (`scripts/file_delivery.py`):**
   - Delivers actual digital files (PDFs, videos, audio, documents, pictures) natively upon confirmed purchase using Telegram's native Bot API (`sendDocument`, `sendVideo`, `sendAudio`, `sendPhoto`).
   - Admins attach files directly via Telegram using `/set_file <id>`.
   - VIP channel memberships automatically skip file delivery and generate single-use invite links instead.
6. **Automatic Blockchain Verification (`scripts/chaincheck.py`):**
   - Direct on-chain verification for manual crypto payments across EVM blockchains (BSC, Ethereum, Polygon) using free public JSON-RPC endpoints.
   - Verifies sender, merchant recipient address, $\ge 2$ block confirmations, and token transfer logs (including BSC USDT 18-decimal precision with 2% price tolerance).
   - If confirmed on-chain, delivery is immediate and automatic; if unmined or pending, orders queue into manual review for admin approval.
7. **Live Crypto Spot Rates (`scripts/prices.py`):**
   - Fetches live cryptocurrency exchange rates via CoinGecko public API (cached 60 seconds) so customers know the exact token amount to transfer.
   - Gracefully falls back to USD amounts if CoinGecko is unreachable.
8. **CoinGate KYC Compliance (`COINGATE_ENABLED`):**
   - CoinGate checkouts require merchant account KYC verification. The CoinGate checkout button is kept hidden unless `COINGATE_ENABLED=1` is explicitly set in `.env`.

---

## 7. Configuring Products & Store Settings

All products and prices are managed directly from Telegram:

### Admin Menu (Interactive Wizard)
Send `/start` to your bot from your owner account → tap **⚙️ Admin Menu**:
- **➕ Add Product** — Step-by-step wizard (name, price, duration, delivery kind).
- **🗑️ Remove Product** — Select a product to remove from catalogue.
- **🛒 List Products** — View current active products.

### Admin Command Shortcuts
- `/products` — List active catalogue.
- `/add_product Name | price [| days [| kind]]` — e.g., `/add_product VIP Month | 12.00 | 30 | channel`
- `/remove_product <id>` — Delete product by ID.
- `/set_deliver <id> <text>` — Set text/link delivered upon purchase.
- `/set_file <id>` — Reply to any file, video, audio, or document with this command to attach a real file for digital delivery.
- `/broadcast <message>` — Send announcement to all active subscribers.
- `/stats` — View sales analytics and subscriber counts.
- `/set_setting <key> <value>` — Update settings (`website_url`, `support_url`, `channel_id`).

---

## 8. VIP Channel Automation (Optional)

To sell access to a private Telegram channel:
1. Add your bot as an **Administrator** in your private channel (with invite users and ban users permissions).
2. Set `CHANNEL_ID=-1001234567890` and `CHANNEL_LINK=https://t.me/yourchannel` in `.env` or via `/set_setting`.
3. The bot automatically generates single-use invite links upon successful payment and sweeps expired subscribers on schedule.

---

## 9. Package File Structure

```text
telstore/
├── README.md               Reference index and technical documentation
├── README.fa.md            Persian documentation for Persian administrators
├── INSTALL.md              Quick-start installation guide
├── DEPLOY_SERVER.md        Full 24/7 server deployment, backup & uninstallation
├── BUYER_GUIDE.md          Buyer onboarding and admin administration walkthrough
├── ARCHITECTURE.md         System architecture and storage guarantees
├── FOR_SELLER.md           Seller package verification and distribution rules
└── scripts/
    ├── bot.py               Main bot polling, command dispatcher, and order state machine
    ├── storage.py           Crash-safe atomic storage engine and concurrency locking
    ├── config.py            Configuration loader, environment isolation & validation
    ├── lang.py              Customer-facing messages, UI strings and button labels
    ├── file_delivery.py     Native file and media delivery engine (sendDocument, sendVideo, etc.)
    ├── chaincheck.py        Automatic EVM on-chain verification for manual crypto transactions
    ├── prices.py            Live cryptocurrency spot prices via CoinGecko public API
    ├── nowpayments.py       NOWPayments card and cryptocurrency payment gateway
    ├── coingate.py          CoinGate hosted web-payment gateway
    ├── admin.py             Admin administration and channel membership management
    ├── channel_access.py    Channel admission and expiration sweep routines
    ├── broadcast.py         Subscriber announcement messaging engine
    ├── deploy_server.sh     Interactive server installer and upgrade manager
    ├── install_telstore.sh  Non-interactive unattended server installer (flags only)
    ├── uninstall_server.sh  Safe server uninstaller with mandatory backup and data preservation
    ├── run_bot.sh           Manual foreground execution script
    ├── check_bot.sh         Health diagnostic and configuration audit tool
    ├── requirements.txt     Development documentation (standard library only at runtime)
    └── .env.example         Configuration template
```

---

## 10. Safe Uninstallation

To safely uninstall the bot and service from your server:

```bash
# Dry-run preview:
bash scripts/uninstall_server.sh --dry-run

# Execute uninstallation:
bash scripts/uninstall_server.sh
```

- Creates an emergency rollback archive (`/tmp/telstore_pre_uninstall_*.tar.gz`).
- Stops and disables `telstore-bot` systemd service.
- Cleans up executable scripts and caches.
- **Strictly preserves** `subscribers.json`, `pending_payments.json`, `manual_orders.json`, `.env`, and all `.bak_*` files.

---

## 11. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `python3 not found` | Python not installed | Run `apt-get update && apt-get install -y python3`. |
| Bot not replying to `/start` | Invalid token or network issue | Check token in `.env`; run `bash scripts/check_bot.sh`. |
| Admin Menu not showing | `OWNER_CHAT_ID` mismatch | Send `/start` from the account matching `OWNER_CHAT_ID` in `.env`. |
| `SingleInstanceLock: already running` | Previous process still running or dead lock | Check `ps aux | grep bot.py`. If stopped, remove `rm -f scripts/bot.lock`. |
| Gateway checkout button hidden | API key unconfigured or CoinGate KYC required | Provide keys in `.env`. For CoinGate, ensure `COINGATE_ENABLED=1`. Restart service: `systemctl restart telstore-bot`. |
| `GatewayConfigurationError` | Environment/key mismatch | Ensure `NOWPAYMENTS_ENVIRONMENT=production` matches live keys. |
| Customer funds not arriving | Unverified payout wallet | Ensure payout wallet is verified in your gateway dashboard. |

---

## 12. Support & Contact

- **Telegram Support:** [@k1_adineh](https://t.me/k1_adineh)
- **License:** Single-site commercial license. Use for your own shop, channel, or commercial bot. Redistribution is strictly prohibited.
