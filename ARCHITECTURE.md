# ARCHITECTURE.md — How the TelStore Bot is built

The bot is a **single Python process** that polls the Telegram Bot API
(`getUpdates`) with the standard library only — no `python-telegram-bot`, no
framework, no external runtime. It works out of the box on any Python 3.8+.

```
                  Telegram servers
                        │  (Bot API: getUpdates / sendMessage / ...)
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
        │  config.py   ← reads .env  (single source)  │
        │  admin.py    ← owner commands & subscribers  │
        │  channel_access.py ← VIP channel membership  │
        │  nowpayments.py   ← NOWPayments gateway      │
        │  coingate.py      ← CoinGate gateway         │
        │  lang.py          ← every user-facing string │
        └───────────────┬─────────────────────────────┘
                        │  runtime JSON files (created/used live)
                        ▼
        subscribers.json   products.json   settings.json
        pending_payments.json   wizard.json
```

## Module responsibilities (single-responsibility)

| File | Responsibility |
|------|----------------|
| `bot.py` | Main entry point. Polling loop, message + callback routing, product wizard, payment-menus. |
| `config.py` | Single source of truth. Loads every setting from `.env` and the runtime JSON files (`products.json`, `settings.json`). |
| `lang.py` | **Every** customer-facing message, button label, and hint lives here in one place. Reword/translate without touching logic. |
| `admin.py` | Owner-only actions: `/stats`, `/broadcast`, `/add_member`, `/kick`, `/set_price`, product add/remove, settings. |
| `channel_access.py` | Automatic VIP channel membership: grant an invite link on payment, kick on expiry. |
| `nowpayments.py` | Creates crypto invoices and checks payment status (auto-delivery). |
| `coingate.py` | Optional hosted web-payment page (order → `payment_url`). |
| `broadcast.py` | Standalone CLI to broadcast a file/message to subscribers. |
| `deploy_server.sh` | One-shot installer: prompts for keys → writes `.env` → installs the `telstore-bot` systemd service. |
| `run_bot.sh` | Runs the bot in the foreground (testing / manual). |
| `check_bot.sh` | Health check: Python, module imports, token validity, payment config, files, service state. |

## Data model (runtime JSON, gitignored)

- **`subscribers.json`** — `{"subscribers": [ {chat_id, username, plan, premium_until, payment_method} ]}`
- **`products.json`** — the owner's catalogue (created on first add; falls back
  to the single default in `config.py`).
- **`settings.json`** — runtime owner-set values (channel, website, support).
- **`pending_payments.json`** — maps chat_id → pending NOWPayments invoice so a
  paid order is delivered exactly once.
- **`wizard.json`** — mid add-product wizard state per owner.

## Payment flow

1. Customer opens `/shop` → picks a product → chooses network / gateway.
2. **NOWPayments** — bot calls `create_payment`/`create_invoice`; customer pays
   on the NOWPayments page (card or crypto). A **background thread** polls the
   status every ~20s and calls `_deliver_product` when finished.
3. **Manual** — bot shows the owner's wallet + amount; customer sends a
   transaction hash; the owner verifies it and the bot grants access.
4. **CoinGate** — bot creates an order and sends the hosted `payment_url`.
5. On success the bot delivers the product (channel invite link or digital
   message) and notifies the owner with the transaction ID.

## Design rules

- **No keys in code.** Everything comes from `.env`.
- **No hard-coded UI strings in logic.** All in `lang.py`.
- **Stdlib only.** No package list to maintain on the server.
- **Runs from Iran / restricted networks** — raw Bot API via `urllib` plus an
  IPv4 patch when needed (see `_ipv4_getaddrinfo` in `bot.py`).