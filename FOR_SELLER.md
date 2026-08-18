# FOR_SELLER.md — Seller's brief (for the person distributing this package)

This file is **for the seller** (the person who sells the TelStore bot). It is
included in the delivery as part of the documentation set. The buyer-facing
documents are `README.md`, `INSTALL.md`, `DEPLOY_SERVER.md`, `BUYER_GUIDE.md`,
and `ARCHITECTURE.md`.

## What you are selling

A complete Telegram bot that lets each buyer run their own crypto-paid shop:
digital products + VIP channel subscriptions. The buyer installs it on their own
server and plugs in **their own** Telegram token, wallet, and NOWPayments /
CoinGate keys.

## What ships to each buyer

The `telstore/` folder contains:

- `README.md`, `INSTALL.md`, `DEPLOY_SERVER.md`, `ARCHITECTURE.md`,
  `BUYER_GUIDE.md`, `FOR_SELLER.md` — the documentation set
- `scripts/` — the full Python source (stdlib only)
  - `bot.py` main bot, `config.py` settings, `lang.py` all UI text,
    `admin.py`, `channel_access.py`, `nowpayments.py`, `coingate.py`,
    `broadcast.py`
  - `deploy_server.sh` one-shot installer (creates the `telstore-bot` systemd
    service), `run_bot.sh`, `check_bot.sh`
  - `.env.example` — template buyers fill with their own keys
  - `requirements.txt` — optional dev deps only (stdlib needed at runtime)

## Branding & cleanliness rules (keep these true on every build)

- **No personal/author keys or IDs anywhere** in the shipped package. All
  secrets must be placeholder values (`your_bot_token_here`, etc.) or read from
  `.env`.
- **No "Crypto Quest", "ADN", "CQB", or other legacy brand names.** The package
  is branded **TelStore**. Search the tree before shipping:
  ```bash
  grep -rin "crypto.quest\|ADN\|cqb" telstore/ 2>/dev/null && echo "found!" || echo "clean"
  ```
- **No Persian in the shipped package.** Everything buyer-facing is English.
- **No runtime data files** (`subscribers.json`, `products.json`,
  `settings.json`, `pending_payments.json`, `wizard.json`) and no `.env` in the
  shipped zip. Those are created live per-buyer, never pre-shipped.
- `deploy_server.sh` and `check_bot.sh` use the service name **`telstore-bot`**
  — keep that consistent with the README when you rebuild.

## Versioning & rebuild checklist

When you build a new sale zip:

1. Copy the working source into a clean build folder.
2. Run the brand-grep above; fix any residue.
3. Confirm only `.env.example` (no `.env`), no runtime JSON, no `__pycache__`.
4. Zip the `telstore/` folder as the root of the archive.
5. Re-verify the archive's contents before uploading.

## Support expectations

Buyers are typically not developers. Expect questions about: getting a bot
token, the chat_id, why the bot isn't answering `/start` (almost always a wrong
token), and how to add their first product. Point them to `BUYER_GUIDE.md` and
`INSTALL.md` first — both are written to be followed without prior knowledge.

## License you pass along

Single-site, non-resellable by the end buyer. Include that wording in the
product description and in `BUYER_GUIDE.md` (already present).