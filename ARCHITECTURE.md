# TelStore Bot — Architecture & Developer Guide

> How the bot is structured and how to extend it. Written for a human developer
> (or a future AI) who picks up this codebase.

## The one-file-per-job rule

Every concern lives in exactly one file. If you need to change something, you
almost always touch **one** file — not three.

```
scripts/
  config.py          settings (read from .env)
  lang.py            every customer-facing string + button label
  bot.py             Telegram logic (polling, menu, payment, dispatch)
  admin.py           owner admin commands
  channel_access.py  auto VIP-channel membership
  nowpayments.py     card/crypto payment gateway
  broadcast.py       cron script that pushes reports to subscribers
  .env               your secrets (gitignored)
```

`lang.py` and `config.py` are **global modules** — every other file imports them.
`bot.py` imports `admin`, `channel_access`, `nowpayments` at the top.

## Configuration (config.py)

All settings are read once at import time from environment variables or the
project `.env` file. Nothing is hard-coded in logic.

| Setting | Env key | Purpose |
|---------|---------|---------|
| `TOKEN` | `TELEGRAM_BOT_TOKEN` | bot token from @BotFather |
| `CRYPTO_ADDRESS` | `CRYPTO_ADDRESS` | payout wallet (EVM) |
| `OWNER_CHAT_ID` | `OWNER_CHAT_ID` | who can use admin commands |
| `CHANNEL_ID` | `CHANNEL_ID` | VIP channel id (auto-membership) |
| `CHANNEL_LINK` | `CHANNEL_LINK` | optional public invite link |
| `NOWPAYMENTS_API_KEY` | `NOWPAYMENTS_API_KEY` | gateway key (empty = disabled) |
| `PRODUCTS` | — | **the product catalogue** (see below) |
| `PREMIUM_DAYS` | — | fallback grant length (legacy) |

### PRODUCTS — your catalogue (multi-product, per-item prices)

`config.PRODUCTS` is a list of dicts. Each entry is one thing the owner sells.
The shop menu is generated automatically from this list — no handler changes
needed to add/remove/reprice a product.

```python
PRODUCTS = [
    {"id": "vip", "name": "VIP Channel", "price_usd": 5.0, "days": 30,
     "kind": "channel", "emoji": "💎",
     "description": "Monthly VIP access"},
    {"id": "guide", "name": "Crypto Guide", "price_usd": 9.99, "days": 0,
     "kind": "digital", "emoji": "📕",
     "description": "PDF guide",
     "deliver": "Here is your PDF: https://example.com/guide.pdf"},
]
```

Fields:
- `id` — unique key, used in callbacks (`prod_<id>`).
- `name` / `emoji` — displayed in the shop.
- `price_usd` — the customer pays **this** amount (any value, per product).
- `days` — how long access lasts; `0` = lifetime / not time-based.
- `kind` — `"channel"` (grant VIP channel access) or `"digital"` (send `deliver`).
- `deliver` — (kind=digital) message/link sent to the buyer after payment.

Helper lookups live here too: `config.get_product(id)` and
`config.get_default_product()`.

## UI text (lang.py)

Every message and button label lives in two dicts:

- `TXT` — full text messages. Placeholders use `{name}` and are filled with
  `.format(...)` in `bot.py`.
- `BTN` — short button labels.

To translate or reword the bot: edit `lang.py` only. Nothing else changes.

## How a payment network is defined (config.py → lang.py)

A network is a dict in `config.CRYPTO_NETWORKS`:

```python
{
    "name": "BSC",
    "standard": "BEP-20",
    "currency": "USDT (BEP-20) / BNB",
    "recommended": True,
    "note": "Recommended - very low fees and fast",
},
```

- `lang.network_button(net)` builds the button label from the dict automatically.
- `lang.network_callback(net)` builds the callback id (`pay_bsc`, etc.).
- `bot.handle_callback` recognises `pay_<network>` and routes to
  `handle_pay_network`.

**To add a new network:** just append a dict to `config.CRYPTO_NETWORKS`.
Buttons and callbacks auto-generate. You do NOT touch `lang.py` or `bot.py`.

## How to add / reprice a product (the important one)

Adding a product = **one dict in `config.PRODUCTS`**. The shop menu, product
page, payment amount, and delivery are all generated from it automatically.

**Add a product:**
```python
PRODUCTS.append({
    "id": "new_thing", "name": "New Thing", "price_usd": 12.50, "days": 0,
    "kind": "digital", "deliver": "Here it is: https://...",
    "description": "What the customer is buying",
})
```
**Reprice an existing product:** change its `"price_usd"` value.

No changes to `bot.py` or `lang.py` are required.

## How to add a new command (example)

1. **Text** → add a key to `lang.TXT` (and a button to `lang.BTN` if it's in a menu).
2. **Logic** → write a `handle_xxx()` function in `bot.py`.
3. **Wire it** → add a branch in `handle_command()` (for `/xxx` slash commands)
   or in `handle_callback()` (for inline buttons).

That's it. `config.py` only changes if the feature needs a new setting.

## Payment flow (for reference)

```
User taps "🛒 Shop"  → handle_shop → shop_keyboard (from config.PRODUCTS)
  → picks a product → handle_product → product page + network_keyboard
    → picks network → handle_pay_network → format_crypto_payment (product price)
      → shows wallet address + the product's price
        → taps "I paid" → handle_pay_done → sends the tx hash
          → /pay <txhash> → handle_pay → _deliver_product
              (channel → grant_channel_access | digital → send "deliver")
```
Bonus path: NOWPayments (`pay_nowpayments[:<product>]` → create invoice →
`check_payment`). The pending record stores the product id so the confirmed
payment delivers the right item.

**Auto-delivery (IPN-like, no server):** the main loop calls
`poll_pending_payments()` every ~20s. For each pending invoice it asks
NOWPayments for the status; when a payment becomes `finished` it delivers the
product automatically and messages the customer — no manual "Check payment
status" tap required. A paid invoice is delivered exactly once (pending is
cleared on delivery).

## Shared logic you should reuse

- `_deliver_product(chat_id, username, product, method)` — the ONLY place that
  records a paid product + delivers it (channel OR digital). Use it instead of
  editing `subscribers.json` directly.
- `grant_channel_access(chat_id)` — grants VIP-channel access and returns the
  text suffix. Called inside `_deliver_product` for `kind="channel"`.
- `_expiry(days)` — ISO expiry for a grant (0 days → lifetime).
- `_finalize_paid_payment(chat_id, payment_id, product_id)` — delivers a
  confirmed NOWPayments payment once + clears it. Used by both the manual
  "Check payment status" button and `poll_pending_payments()`.
- `poll_pending_payments()` — background auto-poll for auto-delivery.

## Rules for contributors

1. Never put UI strings in `bot.py` — they go in `lang.py`.
2. Never re-implement `.env` reading — import `config` and use its values.
3. Add/reprice products in `config.PRODUCTS`, not in `bot.py`.
4. Reuse `_deliver_product` / `grant_channel_access` instead of duplicating.
5. Keep every file to a single responsibility. If a function grows, split it.
6. Run `python -m py_compile *.py` after edits; run the smoke test in
   `PROJECT_STATUS.md#verification` to confirm nothing broke.
