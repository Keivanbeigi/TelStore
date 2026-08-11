# 🖥 Deploy the bot on your own server (24/7)

This bot runs on plain Python and is designed to run as a **24/7 background
service**. You do **not** need your computer to stay on.

> **What you need:** a small Linux VPS (Ubuntu/Debian recommended). Cheapest
> options start around **$2–5/month** (Vultr, DigitalOcean, Contabo, Hostinger,
> Racknerd, etc.). Many accept crypto payment.

---

## Step 1 — Get a VPS & connect

1. Buy a small VPS (1 CPU, 1 GB RAM is plenty).
2. Choose **Ubuntu 22.04/24.04** (or Debian).
3. Connect over SSH from your computer:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```

---

## Step 2 — Copy the bot to the server

From your **local** computer (in a new terminal, NOT the SSH session):

```bash
# where your downloaded crypto-quest-bot folder is
cd /path/to/crypto-quest-bot
scp -r . root@YOUR_SERVER_IP:/root/crypto-quest-bot
```

---

## Step 3 — Run the installer

Back on the **SSH session**:

```bash
cd /root/crypto-quest-bot/scripts
bash deploy_server.sh
```

The script will:
- check/install `python3`
- create a `.env` from `.env.example` (asks you to edit it)
- install a **systemd service** so the bot runs 24/7 and auto-starts on boot
- start the bot

---

## Step 4 — Fill in your `.env`

When the installer creates `.env`, edit it with **your** values:

```bash
nano /root/crypto-quest-bot/.env
```

Set at least:
- `TELEGRAM_BOT_TOKEN` — your bot token from @BotFather
- `CRYPTO_ADDRESS` — your wallet (BSC/ETH/Polygon) where payments go
- `OWNER_CHAT_ID` — your Telegram id (gets the admin panel)

Save (Ctrl+O, Enter, Ctrl+X), then press Enter in the installer to continue.

---

## Step 5 — Manage the bot (useful commands)

```bash
systemctl status crypto-quest-bot      # is it running?
journalctl -u crypto-quest-bot -f      # live logs (Ctrl+C to exit)
systemctl restart crypto-quest-bot     # restart the bot
systemctl stop crypto-quest-bot        # stop it
```

The bot **auto-starts on every reboot** — no need to do anything after a
server restart.

---

## Adding / managing products

From Telegram, as the owner (`OWNER_CHAT_ID`), send:
```
/admin
```
then use the **Add product / Remove product** buttons, or the slash commands:

```
/add_product Name | price | days | kind
/add_product VIP Channel — 1 Month | 5 | 30 | channel
/add_product Crypto Trading E-book | 29 | 0 | digital
/products
/remove_product <id>
```

See `README.md` → **How to add a product** for full details.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `systemctl status` shows `failed` | `journalctl -u crypto-quest-bot -n 50` to see the error |
| Bot token invalid | Check `TELEGRAM_BOT_TOKEN` in `.env` |
| Bot says "ERROR: no token" | `.env` not created — run `bash deploy_server.sh` again |
| Need to change settings | Edit `.env`, then `systemctl restart crypto-quest-bot` |