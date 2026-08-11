# Crypto Quest Bot — Architecture & Developer Guide

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
| `PRICE_USD` | `PRICE_USD` | monthly premium price in USD |
| `CRYPTO_ADDRESS` | `CRYPTO_ADDRESS` | payout wallet (EVM) |
| `OWNER_CHAT_ID` | `OWNER_CHAT_ID` | who can use admin commands |
| `CHANNEL_ID` | `CHANNEL_ID` | VIP channel id (auto-membership) |
| `CHANNEL_LINK` | `CHANNEL_LINK` | optional public invite link |
| `NOWPAYMENTS_API_KEY` | `NOWPAYMENTS_API_KEY` | gateway key (empty = disabled) |
| `PREMIUM_DAYS` | — | length of a Premium grant (default 30) |
| `CRYPTO_NETWORKS` | — | list of payment networks (see below) |

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

## How to add a new command (example)

1. **Text** → add a key to `lang.TXT` (and a button to `lang.BTN` if it's in a menu).
2. **Logic** → write a `handle_xxx()` function in `bot.py`.
3. **Wire it** → add a branch in `handle_command()` (for `/xxx` slash commands)
   or in `handle_callback()` (for inline buttons).

That's it. `config.py` only changes if the feature needs a new setting.

## Payment flow (for reference)

```
User taps "Buy Premium"
  → handle_premium → network_keyboard (from config.CRYPTO_NETWORKS)
    → user picks network → handle_pay_network → format_crypto_payment
      → shows wallet address + instructions
        → user taps "I paid" → handle_pay_done → tells user to send the tx hash
          → user sends /pay <txhash> → handle_pay → _activate_premium + grant_channel_access
```
Bonus path: NOWPayments (`pay_nowpayments` → create invoice → `check_payment`).

## Shared logic you should reuse

- `_activate_premium(chat_id, username, days, method)` — the ONLY place that
  grants Premium. Use it instead of editing `subscribers.json` directly.
- `grant_channel_access(chat_id)` — the ONLY place that grants VIP-channel
  access and returns the text suffix. Use it after any Premium grant.

## Rules for contributors

1. Never put UI strings in `bot.py` — they go in `lang.py`.
2. Never re-implement `.env` reading — import `config` and use its values.
3. Reuse `_activate_premium` / `grant_channel_access` instead of duplicating.
4. Keep every file to a single responsibility. If a function grows, split it.
5. Run `python -m py_compile *.py` after edits; run the smoke test in
   `PROJECT_STATUS.md#verification` to confirm nothing broke.
