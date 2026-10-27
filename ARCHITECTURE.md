# ARCHITECTURE.md — How the TelStore Bot is built

The bot is a **single Python process** that polls the Telegram Bot API
(`getUpdates`) with the standard library only — no `python-telegram-bot`, no
framework, no external runtime. It works out of the box on any Python 3.8+.

```
                  Telegram servers
                        │  (Bot API: getUpdates / sendMessage / sendDocument / ...)
                        ▼
        ┌─────────────────────────────────────────────┐
        │  bot.py  (main process)                     │
        │  - polling loop  (getUpdates)               │
        │  - routes messages → /commands              │
        │  - routes inline-callbacks → menus          │
        │  - background payment poller (thread)       │
        │  - periodic expired-membership sweep        │
        └───────────────┬─────────────────────────────┘
                        │  imports
        ┌───────────────┴─────────────────────────────┐
        │  config.py        ← reads .env (single src) │
        │  storage.py       ← atomic disk & lock      │
        │  admin.py         ← admin cmds & subs       │
        │  file_delivery.py ← real file delivery      │
        │  chaincheck.py    ← EVM on-chain verify     │
        │  prices.py        ← CoinGecko spot rates    │
        │  channel_access.py← VIP channel membership  │
        │  nowpayments.py   ← NOWPayments gateway     │
        │  coingate.py      ← CoinGate gateway        │
        │  lang.py          ← user-facing strings     │
        └───────────────┬─────────────────────────────┘
                        │  runtime JSON files (created/used live)
                        ▼
        subscribers.json      products.json        settings.json
        pending_payments.json manual_orders.json   wizard.json
```

## Module responsibilities (single-responsibility)

| File | Responsibility |
|------|----------------|
| `bot.py` | Main entry point. Polling loop, message + callback routing, product wizard, payment-menus. |
| `config.py` | Single source of truth. Loads every setting from `.env` and the runtime JSON files (`products.json`, `settings.json`). |
| `storage.py` | Crash-safe atomic JSON persistence (`mkstemp`, `fsync`, `os.replace`), file locking (`SingleInstanceLock`), and corruption detection (`DatabaseCorruptedError`). |
| `lang.py` | **Every** customer-facing message, button label, and hint lives here in one place. Reword/translate without touching logic. |
| `admin.py` | Admin-only actions: `/stats`, `/broadcast`, `/add_member`, `/kick`, `/set_price`, product add/remove, `/set_file`, settings. |
| `file_delivery.py` | Inspects Telegram messages for file attachments (`extract_file_ref`), delivers native files via Bot API (`sendDocument`, `sendVideo`, `sendAudio`, `sendPhoto`). |
| `chaincheck.py` | Automatic EVM blockchain verification for manual crypto payments via public JSON-RPC (BSC, ETH, Polygon, $\ge 2$ confirmations, exact match $\pm 0.001$ with unique anti-sniping amount). |
| `prices.py` | Live crypto spot price fetching via CoinGecko public API with in-memory caching and USD fallback. |
| `channel_access.py` | Automatic VIP channel membership: grant an invite link on payment, kick on expiry. |
| `nowpayments.py` | Creates crypto invoices and checks payment status (auto-delivery). |
| `coingate.py` | Optional hosted web-payment page (order → `payment_url`; requires `COINGATE_ENABLED=1`). |
| `broadcast.py` | Standalone CLI to broadcast a file/message to subscribers. |
| `deploy_server.sh` | Interactive installer: prompts for keys, KYC, wallet → writes `.env` → installs `telstore-bot` systemd service. |
| `install_telstore.sh` | Non-interactive unattended installer: accepts flags (`--install-dir`, `--service-name`, `--create-service`, `-y`). |
| `uninstall_server.sh` | Safe server uninstaller with mandatory pre-backup and data preservation (`--keep-data`). |
| `run_bot.sh` | Runs the bot in the foreground (testing / manual). |
| `check_bot.sh` | Health check: Python, module imports, token validity, payment config, files, service state. |

## Data model (runtime JSON, gitignored)

- **`subscribers.json`** — `{"subscribers": [ {chat_id, username, plan, premium_until, payment_method, processed_payments} ]}`
- **`products.json`** — the owner's catalogue (created on first add; falls back to the single default in `config.py`). Supports optional real file delivery references (`file_ref: {kind, file_id, name}`).
- **`settings.json`** — runtime admin-set values (channel, website, support).
- **`pending_payments.json`** — maps chat_id → pending NOWPayments invoice so a paid order is delivered exactly once.
- **`manual_orders.json`** — records manual crypto submissions, transaction hashes, and on-chain verification / admin approval status.
- **`wizard.json`** — mid add-product wizard state per admin.

## Payment flow

1. Customer opens `/shop` → picks a product → chooses network / gateway.
2. **NOWPayments** — bot calls `create_payment`/`create_invoice`; customer pays
   on the NOWPayments page (card or crypto). A **background thread** polls the
   status every ~20s and calls `_deliver_product` when finished.
3. **Manual Crypto** — bot generates a unique payable USD amount (`generate_pay_amount`) with a small 3-decimal fraction (e.g. `$5.037`) to make transactions un-snipable, and persists it to pending payments. It displays the merchant's wallet address and exact live token amount (calculated via `prices.py`). The customer must transfer the exact figure as shown. Customer submits transaction hash (`0x...`). The bot verifies transaction on-chain via `chaincheck.py` using public EVM JSON-RPC:
   - Verifies recipient address matches configured merchant wallet.
   - Verifies transaction is mined with $\ge 2$ block confirmations within a 36-hour wall-clock validity window.
   - Enforces exact amount matching (`exact=True`, strict $\pm 0.001$ window) to prevent front-running / sniping.
   - If confirmed on-chain with exact match: grants instant delivery and notifies admin with expected vs received amounts.
   - If unmined, underpaid, overpaid, or non-matching: transitions to `pending_approval` for one-tap manual review by admin.
4. **CoinGate** — bot creates an order and sends the hosted `payment_url` (active only when `COINGATE_ENABLED=1`).
5. On success the bot delivers the product (real file via `file_delivery.py` or channel single-use invite link) and notifies the admin with the transaction ID.

## Design rules

- **No keys in code.** Everything comes from `.env`.
- **No hard-coded UI strings in logic.** All in `lang.py`.
- **Stdlib only.** No package list to maintain on the server.
- **Runs from Iran / restricted networks** — raw Bot API via `urllib` plus an
  IPv4 patch when needed (see `_ipv4_getaddrinfo` in `bot.py`).
