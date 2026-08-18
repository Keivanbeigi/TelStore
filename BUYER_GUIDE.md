# BUYER_GUIDE.md — Welcome 👋

Thank you for buying the **TelStore Bot**. This guide explains what you received,
what you can do with it, and how to go from zero to a selling shop.

## What you just bought

You bought the **bot software** — a complete, ready-to-deploy Telegram shop that
sells digital products and VIP channel access with crypto payments. It belongs
to **you**: you install it on your own server, connect **your** Telegram bot,
**your** wallet and **your** payment accounts, and sell **your own products** to
**your customers**.

> The price you paid to buy this bot is not part of the code. It only appears
> on the seller's checkout page. Nothing here tracks, phones home, or sends any
> buyer funds to anyone but you.

## Files you received

```
telstore/
├── README.md            Overview + full documentation index
├── INSTALL.md           Quick-start install
├── DEPLOY_SERVER.md     Full 24/7 server deployment
├── ARCHITECTURE.md      How the code is organised
├── BUYER_GUIDE.md       This file
├── FOR_SELLER.md        How to run your own seller operation
└── scripts/             The bot itself (source + .env.example)
```

## Your first 15 minutes

1. **Get a bot token** — open [@BotFather](https://t.me/BotFather) →
   `/newbot` → copy the token.
2. **Get your chat_id** — message [@userinfobot](https://t.me/userinfobot).
3. **(Recommended) run the installer on a server:**
   ```bash
   cd telstore
   bash scripts/deploy_server.sh
   ```
   Enter your token, owner id, wallet and NOWPayments key when asked.
4. **Verify** — `bash scripts/check_bot.sh`, then send `/start` to your bot.

New to servers? Read **INSTALL.md** and **DEPLOY_SERVER.md** first — they walk
you through every step, no prior experience needed.

## Setting up your own shop (owner)

Because you are the owner, your bot shows an extra **⚙️ Owner Menu** that normal
visitors never see. Tap it to:

- **➕ Add Product** (name, price, duration, delivery type — a tap-through wizard)
- **🗑️ Remove Product**, **🛒 List Products**
- Set **website / support / channel** links

You can manage products from a chat too:

```
/products                       show your catalogue
/add_product VIP Year | 49.99 | 365 | channel
/remove_product <your_id>
/broadcast <message>            message all subscribers
/stats                          sales & subscriber numbers
```

Full owner tooling is documented in **README.md** → "Configure your own
products & prices".

## Common questions

- **Do I need coding skills?** No. Everything is configured from Telegram and
  `.env`. The code is clean and commented if you ever want to extend it.
- **Can I change what customers see?** Yes — every message and button label
  lives in one file, `scripts/lang.py`.
- **Where does the money go?** To **your** wallet / your NOWPayments /
  CoinGate account. This bot never touches buyer funds.
- **Does it run forever?** Yes, when installed as the `telstore-bot` systemd
  service it runs 24/7 and restarts on reboot.

## Support & license

- **License:** single-site. Use it for your own shop / channel / business.
  Reselling or redistributing the bot itself is not permitted.
- For help: see **README.md** → Troubleshooting, then contact the seller for
  anything not covered.