# BUYER_GUIDE.md — Welcome 👋

Thank you for buying the **TelStore Bot**. This guide explains what you received,
what you can do with it, and how to go from zero to a live, automated shop.

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

```text
telstore/
├── README.md            Overview + full technical documentation index
├── README.fa.md         Persian documentation guide
├── INSTALL.md           Quick-start installation guide
├── DEPLOY_SERVER.md     Full 24/7 server deployment, backup & uninstallation
├── ARCHITECTURE.md      System architecture and storage guarantees
├── BUYER_GUIDE.md       This guide
├── FOR_SELLER.md        Seller's packaging and rebuild checklist
└── scripts/             The bot itself (source code + .env.example)
    ├── bot.py           Main bot logic and payment processing
    ├── storage.py       Crash-safe atomic storage engine
    ├── config.py        Configuration and environment validation
    ├── lang.py          All customer-facing texts and button labels
    ├── nowpayments.py   NOWPayments card/crypto checkout gateway
    ├── coingate.py      CoinGate crypto web checkout gateway
    ├── admin.py         Owner administration and stats
    ├── channel_access.py VIP channel access controller
    ├── file_delivery.py Real digital product file extraction and delivery
    ├── chaincheck.py    Direct EVM JSON-RPC blockchain verification
    ├── prices.py        Live CoinGecko spot rates and crypto formatting
    ├── broadcast.py     Subscriber broadcast tool
    ├── deploy_server.sh Interactive installer and upgrade manager
    ├── install_telstore.sh Non-interactive scripted server installer
    ├── uninstall_server.sh Safe uninstaller with data protection
    ├── check_bot.sh     Health and diagnostic checker
    └── run_bot.sh       Manual foreground runner
```

## Your first 15 minutes

1. **Get a bot token** — open [@BotFather](https://t.me/BotFather) →
   `/newbot` → copy the token.
2. **Get your chat_id** — message [@userinfobot](https://t.me/userinfobot).
3. **(Recommended) run the installer on your Linux server:**
   ```bash
   cd telstore
   bash scripts/deploy_server.sh
   ```
   Enter your token, owner id, wallet, payment keys, and KYC status when prompted.
4. **Verify** — `bash scripts/check_bot.sh`, then send `/start` to your bot in Telegram.

New to servers? Read **INSTALL.md** and **DEPLOY_SERVER.md** first — they walk
you through every step, no prior experience needed.

## Setting up your shop (as Owner)

Because you are the owner, your bot shows an extra **⚙️ Admin Menu** button that normal
visitors never see. Tap it to:

- **➕ Add Product** (category, name, model, price, duration, delivery kind, file upload, discount — an 8-step wizard)
- **🗑️ Remove Product**, **🛒 List Products**
- Set **website / support / VIP channel** links

You can also manage products directly using chat commands:

```text
/products                       show your catalogue
/add_product VIP Year | 49.99 | 365 | channel
/remove_product <product_id>
/set_deliver <id> <text>        set delivery message/link
/set_file <product_id>          upload or replace digital product file
/broadcast <message>            message all active subscribers
/stats                          sales & subscriber metrics
```

Full admin tooling is documented in **README.md** → "Configuring Products & Store Settings".

## Key Shipped Capabilities

### 1. Real File Delivery (`scripts/file_delivery.py`)
Digital products can deliver **real files** directly to buyers:
- When adding a **digital** product in the Admin Menu wizard (Step 7/8), you are asked to upload the file (PDF, video, audio, photo, or document).
- When a buyer purchases a digital product, the bot sends the actual file using Telegram's API (`sendDocument`, `sendVideo`, `sendAudio`, `sendPhoto`). If sending fails, it falls back to the text message so buyers always receive their purchase.
- **Channel** products skip this step entirely and deliver an exclusive invite link instead.
- You can update any product's file anytime by sending `/set_file <id>`.

### 2. Automatic Blockchain Verification (`scripts/chaincheck.py`)
Direct crypto payments to your wallet are verified on-chain automatically:
- When a buyer pays and submits their transaction hash (TXID), the bot queries public EVM JSON-RPC nodes (BSC, Ethereum, Polygon, testnets) with **no third-party API keys or ports required**.
- The bot confirms that the transaction was mined (`status == 1`), has reached at least **2 block confirmations**, was sent to your configured merchant address, and covers the required price within a 2% exchange tolerance.
- Token decimals are resolved automatically: **USDT on BSC (BEP-20) uses 18 decimals** (`0x55d398326f99059ff775485246999027b3197955`), while Ethereum/Polygon USDT uses 6 decimals. Native coin payments (BNB, ETH, POL) are fully supported.
- **Instant Delivery:** If verified on-chain, access or files are delivered immediately without admin intervention.
- **Fail-Closed Forwarding:** If a transaction is unmined, underpaid, sent to the wrong wallet, or uses an invalid hash, it creates a `pending_approval` order and alerts the admin with the reason so you can review and approve/reject with one click.

### 3. Live Cryptocurrency Price Quotes (`scripts/prices.py`)
- The bot retrieves live USD spot rates from the CoinGecko public API with an 8-second timeout.
- The direct crypto payment page quotes the exact coin amount (e.g. `0.05 BNB`) alongside the USD price (`~$30.00 USD`).
- If CoinGecko is unreachable or rate-limited, the bot gracefully falls back to displaying the USD-only amount (`$30.00`) without crashing.

### 4. Server Management Scripts
- **`scripts/deploy_server.sh`** — Interactive installer with credential prompts, backup creation, and systemd registration.
- **`scripts/install_telstore.sh`** — Non-interactive installer using command-line flags for automated deployments.
- **`scripts/uninstall_server.sh`** — Safe uninstaller with pre-removal backup archive and data preservation.
- **`scripts/check_bot.sh`** — System health check and diagnostic tool.

## Common questions

- **Do I need coding skills?** No. Everything is configured from Telegram and
  `.env`. The code is clean and commented if you ever want to inspect or extend it.
- **Can I change what customers see?** Yes — every customer message and button label
  lives in one file: `scripts/lang.py`.
- **Where does the money go?** Directly to **your** wallet or your NOWPayments /
  CoinGate account. The bot never routes buyer funds through intermediate servers.
- **Does it run forever?** Yes. When installed as the `telstore-bot` systemd
  service, it runs 24/7 and restarts automatically if the server reboots.
- **How do I safely uninstall if needed?** Run `bash scripts/uninstall_server.sh`. It
  backs up your directory, stops the service, cleans code, and **strictly preserves**
  all customer databases and `.env` files.

## Support & license

- **License:** Single-site commercial license. Use it for your own shop / channel / business.
  Reselling or redistributing the bot codebase itself is strictly prohibited.
- **Support:** See **README.md** → Troubleshooting, or contact [@k1_adineh](https://t.me/k1_adineh) on Telegram.
