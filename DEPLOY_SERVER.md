# DEPLOY_SERVER.md — Deploy the TelStore Bot to a 24/7 server

The bot is a plain Python 3 program that polls the Telegram Bot API. To sell
around the clock it must run on an always-on server. This guide steps you
through a full deployment to any Ubuntu/Debian VPS.

> Two ways to run: **[A] the one-command installer** (recommended, ~1 minute)
> or **[B] fully manual**. Both produce the same running bot; use A unless you
> need to customise.

---

## Part A — One-command installer (recommended)

### A0. Copy the package to your server

From your **own computer** (a terminal):

```bash
scp -r telstore root@YOUR_SERVER_IP:~/
```

Replace `YOUR_SERVER_IP` with your server's public IP. (WinSCP / FileZilla:
just drag the `telstore` folder into your home directory.)

### A1. Log in

```bash
ssh root@YOUR_SERVER_IP
cd ~/telstore
```

### A2. Run the installer

```bash
bash scripts/deploy_server.sh
```

Answer the prompts with **your** values: bot token, owner chat_id, EVM wallet
(optional), NOWPayments API key (optional).

The script does everything:

- checks/installs Python 3
- writes a `.env` with your settings
- installs a **systemd service** named `telstore-bot`
- starts it now and enables it to start on every boot

You should see: `✅ Bot service is RUNNING.`

### A3. Verify

```bash
bash scripts/check_bot.sh
systemctl status telstore-bot
```

Then open Telegram → send `/start` → your bot replies with the main menu.

---

## Part B — Manual deployment

If you prefer to run it yourself (e.g. on WSL or a container):

```bash
cd telstore
cp scripts/.env.example .env
nano .env                       # fill in your token, owner id, wallet, keys
python3 -m pip install -r requirements.txt || true   # stdlib only, optional
bash scripts/run_bot.sh         # foreground; Ctrl+C stops it
```

For a persistent background process you can wrap `run_bot.sh` with your own
`nohup`, Docker, or supervisor.

---

## Day-to-day management

| Task | Command |
|------|---------|
| Is it running? | `systemctl status telstore-bot` |
| Live logs | `journalctl -u telstore-bot -f`  *(Ctrl+C to exit)* |
| Restart after a `.env` edit | `systemctl restart telstore-bot` |
| Auto-start on boot | done by the installer (`enable`) |

---

## Editing settings later

All keys live in `.env` (created by the installer in the project root):

- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `CRYPTO_ADDRESS` — EVM wallet for manual BSC/ETH/Polygon payments
- `NOWPAYMENTS_API_KEY` — automatic card/crypto checkout
- `COINGATE_AUTH_TOKEN` — optional 2nd web-payment option
- `OWNER_CHAT_ID` / `TELEGRAM_CHAT_ID` — your owner id (admin panel)
- `CHANNEL_ID` / `CHANNEL_LINK` — optional VIP channel
- `WEBSITE_URL` / `SUPPORT_URL` — shown to customers

After editing: `systemctl restart telstore-bot`.

---

## Common issues

- **`python3 not found`** → `apt-get update && apt-get install -y python3`
- **Bot silent after `/start`** → re-check the token in `.env`, then `bash scripts/check_bot.sh`
- **`systemctl restart` says unit not found** → you used `run_bot.sh`, not the installer; run Part A.