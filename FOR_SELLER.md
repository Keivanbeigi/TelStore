# FOR_SELLER.md — Seller's Brief (Distribution & Quality Assurance)

This file is **for the seller** (the person distributing the TelStore bot package). It is
included in the delivery as part of the operational documentation set. The buyer-facing
documents are `README.md`, `INSTALL.md`, `DEPLOY_SERVER.md`, `BUYER_GUIDE.md`,
and `ARCHITECTURE.md`.

## What You Are Selling

A complete, production-hardened Telegram bot enabling buyers to run their own crypto-paid shop:
digital goods + automated VIP channel subscriptions. The buyer installs it on their own
Linux server and connects **their own** Telegram bot token, EVM wallet, and NOWPayments /
CoinGate accounts.

## What Ships to Each Buyer

The `telstore/` directory contains:

- `README.md`, `README.fa.md`, `INSTALL.md`, `DEPLOY_SERVER.md`, `ARCHITECTURE.md`,
  `BUYER_GUIDE.md`, `FOR_SELLER.md` — full documentation set
- `scripts/` — complete Python source (standard library only)
  - `bot.py` — main bot polling loop, command dispatcher, and payment state machine
  - `storage.py` — crash-safe atomic disk persistence engine and OS process locking
  - `config.py` — configuration loading, strict environment validation and decimals
  - `lang.py` — UI strings and customer-facing message templates
  - `file_delivery.py` — native file and media delivery engine (`sendDocument`, `sendVideo`, etc.)
  - `chaincheck.py` — public EVM JSON-RPC automatic on-chain payment verification
  - `prices.py` — live CoinGecko crypto spot price fetcher and formatter
  - `nowpayments.py` — NOWPayments card and crypto gateway module
  - `coingate.py` — CoinGate web payment gateway module
  - `admin.py` — admin administration panel and stats
  - `channel_access.py` — VIP channel member controller
  - `broadcast.py` — mass subscriber notification tool
  - `deploy_server.sh` — interactive server installer and upgrade manager
  - `install_telstore.sh` — non-interactive unattended server installer (flags only)
  - `uninstall_server.sh` — safe server uninstaller with mandatory backup & data preservation
  - `check_bot.sh` — diagnostic health self-test
  - `run_bot.sh` — manual foreground runner
  - `.env.example` — configuration template with sanitized placeholders
  - `requirements.txt` — documentation note (Python standard library only)

## Branding & Cleanliness Rules (Enforce on Every Release Build)

- **Zero hardcoded secrets or author keys:** All API keys, chat IDs, and tokens in shipped files must be generic placeholders (`your_bot_token_here`, etc.).
- **No legacy branding:** The package is branded strictly **TelStore**. No traces of legacy project names.
- **English buyer documents:** Core buyer guides (`README.md`, `INSTALL.md`, `DEPLOY_SERVER.md`, `BUYER_GUIDE.md`) are in English. `README.fa.md` is provided as a supplementary guide for Persian administrators.
- **Zero runtime data files in shipped archive:** No `subscribers.json`, `pending_payments.json`, `manual_orders.json`, `products.json`, `settings.json`, `bot.lock`, `*.bak_*`, or `.env` in the clean distribution archive. These are generated dynamically upon installation.
- **Systemd service consistency:** Ensure `deploy_server.sh`, `install_telstore.sh`, `uninstall_server.sh`, `check_bot.sh`, and documentation all reference `telstore-bot` as the canonical service name.

## Release Packaging Checklist

Before archiving a new distribution zip:

1. Copy source files into a clean build directory.
2. Verify all tests pass (`test_installer_flow.py`, `test_file_delivery.py`, `test_chain_verify.py`, `test_prices.py`, `test_uninstaller.py`, regression suites).
3. Confirm absence of `.env`, `*.json` runtime databases, and `__pycache__`.
4. Run syntax verification: `python3 -m py_compile scripts/*.py`.
5. Create clean archive: `zip -r telstore_v1.1.0.zip telstore/`.
6. Inspect archive table of contents to ensure no sensitive files are bundled.
