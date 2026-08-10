#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crypto Quest Telegram bot - subscription manager with inline menu
==================================================================
Polling bot (raw Bot API via urllib - works from Iran, no python-telegram-bot).
Interactive inline keyboard menu that routes customers straight to crypto payment.
All customer-facing text is in ENGLISH (product is sold via an international website).

Commands:
  /start        - show main menu
  /subscribe    - free plan
  /premium      - premium plan (crypto payment)
  /pay <txhash> - confirm crypto payment with transaction hash
  /unsubscribe  - cancel subscription
  /status       - subscription status
  /help         - help

Inline keyboard callbacks (data):
  menu            - back to main menu
  sub_free        - subscribe free plan
  premium         - show premium / payment page
  pay_bsc         - BSC payment instructions
  pay_eth         - Ethereum payment instructions
  pay_poly        - Polygon payment instructions
  pay_nowpayments - create a NOWPayments crypto invoice (card/crypto)
  pay_done        - "I paid" -> asks for tx hash
  status          - subscription status
  unsubscribe     - cancel subscription

Runs:
  python bot.py
"""
import json
import os
import re
import sys
import time
import datetime
import urllib.request
import urllib.parse

import nowpayments  # crypto payment gateway (optional)

# ------------------------------------------------------------
#  Config
# ------------------------------------------------------------
def _env_file():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def _load_env_str(key, default=""):
    """Read a string value from env or the project .env file."""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    env_path = _env_file()
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8-sig") as f:
                m = re.search(rf'^{key}=([^\r\n]+)', f.read(), re.M)
            if m:
                return m.group(1).strip().strip('"').strip("'")
        except Exception:
            pass
    return default

def _load_env_float(key, default=5.0):
    try:
        return float(_load_env_str(key, str(default)))
    except ValueError:
        return default

def _load_token():
    """Read TELEGRAM_BOT_TOKEN from env or the project .env file."""
    return _load_env_str("TELEGRAM_BOT_TOKEN")

TOKEN = _load_token()
SUBSCRIBERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscribers.json")

# Configurable via .env (this bot is a sellable template - each buyer sets their own)
PRICE_CRYPTO_USD = _load_env_float("PRICE_USD", 5.0)          # $/month
CRYPTO_ADDRESS = _load_env_str(
    "CRYPTO_ADDRESS",
    "0xB20c44e0C5deef5c7ba5293D6eBE4Af278B836cD")             # payout wallet (buyer's)

# Supported networks (BSC first and recommended). Only BSC gets the recommended badge.
CRYPTO_NETWORKS = [
    {
        "name": "BSC",
        "standard": "BEP-20",
        "currency": "USDT (BEP-20) / BNB",
        "recommended": True,
        "note": "Recommended - very low fees and fast",
        "recommended_label": "⭐ Recommended",
    },
    {
        "name": "Ethereum",
        "standard": "ERC-20",
        "currency": "USDT (ERC-20) / ETH",
        "recommended": False,
        "note": "Secure but higher gas fees",
        "recommended_label": "",
    },
    {
        "name": "Polygon",
        "standard": "MATIC",
        "currency": "USDC / POL",
        "recommended": False,
        "note": "Low fees, Layer 2 network",
        "recommended_label": "",
    },
]

def get_recommended_network():
    """Return the recommended network (BSC)."""
    for n in CRYPTO_NETWORKS:
        if n.get("recommended"):
            return n
    return CRYPTO_NETWORKS[0]

def format_crypto_payment(network=None):
    """Build the full crypto payment guide for a given network (default: recommended)."""
    if network is None:
        network = get_recommended_network()
    flag = network.get("recommended_label", "")
    flag_str = flag + " " if flag else ""
    lines = [f"💰 Price: ${PRICE_CRYPTO_USD}/month",
             "",
             f"🌐 Network: {flag_str}{network['name']} ({network['standard']})",
             f"   Token: {network['currency']}",
             f"   {network['note']}",
             "",
             "🏦 Wallet address (all networks):",
             f"`{CRYPTO_ADDRESS}`",
             "",
             "📤 Send exactly $5 worth (plus network fee).",
             "",
             "✅ After paying, tap \"I paid\" and send the transaction hash.",
             ""]
    return "\n".join(lines)

def network_keyboard():
    """Inline keyboard with network options for payment."""
    rows = []
    for n in CRYPTO_NETWORKS:
        if n["name"] == "BSC":
            label = f"⭐ {n['name']} (Recommended)"
        elif n["name"] == "Ethereum":
            label = "Ethereum (ERC-20)"
        else:
            label = "Polygon (MATIC)"
        rows.append([{"text": label, "callback_data": f"pay_{n['name'].lower()}"}])
    rows.append([{"text": "💳 Pay with Card / Crypto (NOWPayments)", "callback_data": "pay_nowpayments"}])
    rows.append([{"text": "◀️ Back to menu", "callback_data": "menu"}])
    return {"inline_keyboard": rows}

def main_menu_keyboard():
    """Main menu inline keyboard."""
    return {
        "inline_keyboard": [
            [{"text": "💎 Buy Premium - $5/month", "callback_data": "premium"}],
            [{"text": "🆓 Free Subscription", "callback_data": "sub_free"}],
            [{"text": "📊 Subscription Status", "callback_data": "status"}],
            [{"text": "❓ Help", "callback_data": "help"}],
            [{"text": "🚫 Unsubscribe", "callback_data": "unsubscribe"}],
        ]
    }

def pay_done_keyboard():
    """Keyboard shown after a payment is submitted."""
    return {
        "inline_keyboard": [
            [{"text": "✅ I paid", "callback_data": "pay_done"}],
            [{"text": "◀️ Back to menu", "callback_data": "menu"}],
        ]
    }

def back_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "◀️ Back to menu", "callback_data": "menu"}],
        ]
    }

# ------------------------------------------------------------
#  Persistence
# ------------------------------------------------------------
def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"subscribers": []}

def save_subscribers(data):
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_subscriber(data, chat_id):
    for s in data["subscribers"]:
        if str(s.get("chat_id")) == str(chat_id):
            return s
    return None

# ------------------------------------------------------------
#  Bot API helpers (raw urllib - works from Iran)
# ------------------------------------------------------------
def api_call(method, **params):
    """Call a Telegram Bot API method. Returns parsed JSON or None on error."""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"api error [{method}]:", e)
        return None

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    """Send a message with optional inline keyboard."""
    params = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        params["reply_markup"] = json.dumps(reply_markup)
    if parse_mode:
        params["parse_mode"] = parse_mode
    return api_call("sendMessage", **params)

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    """Edit an existing message (used to replace menu after a button tap)."""
    params = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        params["reply_markup"] = json.dumps(reply_markup)
    if parse_mode:
        params["parse_mode"] = parse_mode
    return api_call("editMessageText", **params)

def answer_callback(callback_query_id, text=None):
    """Acknowledge a button tap (required to stop Telegram's loading spinner)."""
    params = {"callback_query_id": callback_query_id}
    if text:
        params["text"] = text
    return api_call("answerCallbackQuery", **params)

def get_updates(offset):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=25&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("result", [])
    except Exception as e:
        print("getUpdates error:", e)
        return []

# ------------------------------------------------------------
#  Handlers
# ------------------------------------------------------------
def main_menu_text():
    return ("👋 Welcome to Crypto Quest!\n\n"
            "Get daily reports on XP farming missions and badges.\n"
            "Choose an option below to get started 👇")

def show_main_menu(chat_id, message_id=None):
    text = main_menu_text()
    if message_id is not None:
        return edit_message(chat_id, message_id, text, main_menu_keyboard())
    return send_message(chat_id, text, main_menu_keyboard())

def handle_subscribe(chat_id, username, data):
    sub = find_subscriber(data, chat_id)
    if sub:
        text = "✅ You are already subscribed! Check your status below 👇"
        return send_message(chat_id, text, back_menu_keyboard())
    data["subscribers"].append({
        "chat_id": str(chat_id),
        "username": username or "",
        "plan": "free",
        "subscribed_at": datetime.datetime.now().isoformat(),
        "premium_until": None,
        "payment_method": None,
    })
    save_subscribers(data)
    text = ("🆓 Free subscription activated!\n"
            "You'll receive a weekly missions report.\n\n"
            "💎 For the daily report (every 6 hours), tap \"Buy Premium\".")
    return send_message(chat_id, text, back_menu_keyboard())

def handle_premium(chat_id, message_id=None):
    sub_data = load_subscribers()
    sub = find_subscriber(sub_data, chat_id)
    if sub and sub.get("plan") == "premium":
        until = sub.get("premium_until", "unknown")
        text = f"💎 You are Premium until {until}"
    else:
        text = ("💎 Premium subscription - daily report every 6 hours\n"
                f"💰 Price: ${PRICE_CRYPTO_USD}/month\n\n"
                "Select your payment network:")
    if message_id is not None:
        return edit_message(chat_id, message_id, text, network_keyboard())
    return send_message(chat_id, text, network_keyboard())

def handle_pay_network(chat_id, message_id, network_name):
    network = None
    for n in CRYPTO_NETWORKS:
        if n["name"].lower() == network_name:
            network = n
            break
    if network is None:
        network = get_recommended_network()
    text = format_crypto_payment(network)
    return edit_message(chat_id, message_id, text, pay_done_keyboard(), parse_mode="Markdown")

def handle_pay_done(chat_id, message_id):
    text = ("✅ Great! Send the amount to the wallet address above.\n\n"
            "After the transaction, send the **tx hash** here to confirm.")
    return edit_message(chat_id, message_id, text, back_menu_keyboard())

def handle_nowpayments(chat_id, message_id):
    """Create a NOWPayments invoice so the customer pays to the owner's account."""
    if not nowpayments.is_configured():
        text = ("💳 Card / crypto payments coming soon!\n\n"
                "For now, use the manual wallet address from the network options "
                "below to pay directly.")
        return edit_message(chat_id, message_id, text, network_keyboard())

    # USDT on TRON (low fees, widely supported) as the default pay currency.
    payment = nowpayments.create_payment(
        price_usd=PRICE_CRYPTO_USD,
        pay_currency="usdttrc20",
        order_id=f"cq-{chat_id}-{int(time.time())}",
        description="Crypto Quest Premium - 30 days",
    )
    text = nowpayments.format_payment_instructions(payment)
    if "Invoice" in text:
        # Remember this pending payment for status checks.
        _save_pending(chat_id, payment.get("payment_id"))
        return edit_message(chat_id, message_id, text, pay_check_keyboard(), parse_mode="Markdown")
    return edit_message(chat_id, message_id, text, back_menu_keyboard())

# --- pending NOWPayments invoices (chat_id -> payment_id) ---
PENDING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pending_payments.json")

def _load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_pending(chat_id, payment_id):
    data = _load_pending()
    data[str(chat_id)] = str(payment_id)
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pay_check_keyboard():
    """Keyboard for a created NOWPayments invoice."""
    return {
        "inline_keyboard": [
            [{"text": "🔎 Check payment status", "callback_data": "check_payment"}],
            [{"text": "◀️ Back to menu", "callback_data": "menu"}],
        ]
    }

def handle_check_payment(chat_id, username, message_id):
    """Check the status of the customer's pending NOWPayments invoice."""
    pending = _load_pending()
    payment_id = pending.get(str(chat_id))
    if not payment_id:
        text = "No pending payment found. Tap \"Buy Premium\" to start a new one."
        return edit_message(chat_id, message_id, text, back_menu_keyboard())

    status = nowpayments.get_payment_status(payment_id)
    # NOWPayments returns {'payment_status': 'finished'|'waiting'|'confirming'|...}
    state = status.get("payment_status", "unknown") if isinstance(status, dict) else "unknown"

    if state == "finished":
        # Payment confirmed -> activate premium for 30 days.
        data = load_subscribers()
        sub = find_subscriber(data, chat_id)
        until = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
        if not sub:
            data["subscribers"].append({
                "chat_id": str(chat_id), "username": username or "",
                "plan": "premium", "subscribed_at": datetime.datetime.now().isoformat(),
                "premium_until": until, "payment_method": "nowpayments",
            })
        else:
            sub["plan"] = "premium"
            sub["premium_until"] = until
            sub["payment_method"] = "nowpayments"
        save_subscribers(data)
        _save_pending(chat_id, "")  # clear pending
        text = ("✅ Payment confirmed! 🎉\n"
                "Your Premium is now active for 30 days.")
        return edit_message(chat_id, message_id, text, back_menu_keyboard())

    if state in ("waiting", "confirming", "partially_paid", "expired"):
        text = (f"⏳ Payment status: **{state}**\n\n"
                "Send the exact amount to the address above, then check again "
                "in a minute.")
        return edit_message(chat_id, message_id, text, pay_check_keyboard(), parse_mode="Markdown")

    text = ("⚠️ Could not check payment status. Please try again in a moment.")
    return edit_message(chat_id, message_id, text, pay_check_keyboard())

def handle_status(chat_id, message_id=None):
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    if not sub:
        text = "You are not subscribed. Tap \"Free Subscription\" to start."
    else:
        plan = "💎 Premium" if sub.get("plan") == "premium" else "🆓 Free"
        until = sub.get("premium_until", "—")
        text = (f"📊 Subscription status:\n\n"
                f"Plan: {plan}\n"
                f"Member since: {sub.get('subscribed_at', '—')[:10]}\n"
                f"Premium until: {until}")
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())

def handle_help(chat_id, message_id=None):
    text = ("❓ Help:\n\n"
            "💎 Buy Premium - daily report every 6 hours ($5/month)\n"
            "🆓 Free subscription - weekly report\n"
            "📊 Status - your subscription info\n"
            "🚫 Unsubscribe - cancel membership\n\n"
            "To pay with crypto, pick a network and send the amount to the wallet address.")
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())

def handle_unsubscribe(chat_id, message_id=None):
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    if sub:
        data["subscribers"] = [s for s in data["subscribers"] if str(s.get("chat_id")) != str(chat_id)]
        save_subscribers(data)
        text = "🚫 Your subscription has been cancelled."
    else:
        text = "You are not subscribed."
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())

def handle_pay(chat_id, username, data, txhash):
    sub = find_subscriber(data, chat_id)
    if not sub or sub.get("plan") != "premium":
        if not sub:
            data["subscribers"].append({
                "chat_id": str(chat_id), "username": username or "",
                "plan": "premium", "subscribed_at": datetime.datetime.now().isoformat(),
                "premium_until": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
                "payment_method": "crypto",
            })
        else:
            sub["plan"] = "premium"
            sub["premium_until"] = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            sub["payment_method"] = "crypto"
        save_subscribers(data)
    send_message(chat_id, f"✅ Crypto payment received! (tx: {txhash[:20]}...)\n"
                          f"Your Premium is active for 30 days. Awaiting final confirmation.",
                 back_menu_keyboard())

def handle_callback(chat_id, message_id, callback_id, username, cb_data):
    """Handle inline keyboard button taps."""
    answer_callback(callback_id)  # acknowledge silently (no popup/checkmark)
    data = load_subscribers()

    if cb_data == "menu":
        show_main_menu(chat_id, message_id)
    elif cb_data == "sub_free":
        handle_subscribe(chat_id, username, data)
    elif cb_data == "premium":
        handle_premium(chat_id, message_id)
    elif cb_data in ("pay_bsc", "pay_ethereum", "pay_polygon"):
        net = cb_data.split("_")[1]
        handle_pay_network(chat_id, message_id, net)
    elif cb_data == "pay_nowpayments":
        handle_nowpayments(chat_id, message_id)
    elif cb_data == "check_payment":
        handle_check_payment(chat_id, username, message_id)
    elif cb_data == "pay_done":
        handle_pay_done(chat_id, message_id)
    elif cb_data == "status":
        handle_status(chat_id, message_id)
    elif cb_data == "help":
        handle_help(chat_id, message_id)
    elif cb_data == "unsubscribe":
        handle_unsubscribe(chat_id, message_id)

def handle_command(chat_id, username, command):
    data = load_subscribers()

    if command == "/start":
        show_main_menu(chat_id)
    elif command == "/subscribe":
        handle_subscribe(chat_id, username, data)
    elif command == "/premium":
        handle_premium(chat_id)
    elif command.startswith("/pay "):
        txhash = command.split(" ", 1)[1].strip()
        handle_pay(chat_id, username, data, txhash)
    elif command == "/unsubscribe":
        handle_unsubscribe(chat_id)
    elif command == "/status":
        handle_status(chat_id)
    elif command == "/help":
        handle_help(chat_id)
    else:
        send_message(chat_id, "❓ Unknown command. Choose from the menu.", main_menu_keyboard())

# ------------------------------------------------------------
#  Main polling loop
# ------------------------------------------------------------
def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    print("✅ Bot running... (polling with inline menu)")
    # Drain any stale/old updates so we don't reply to expired callbacks (fixes 400).
    offset = 0
    stale = get_updates(offset)
    for upd in stale:
        offset = max(offset, upd.get("update_id", 0) + 1)
    if stale:
        print(f"   Drained {len(stale)} stale update(s); starting at offset {offset}")
    while True:
        try:
            updates = get_updates(offset)
            for upd in updates:
                update_id = upd.get("update_id", 0)
                offset = update_id + 1

                # Inline button tap
                cq = upd.get("callback_query")
                if cq:
                    chat_id = cq.get("message", {}).get("chat", {}).get("id")
                    message_id = cq.get("message", {}).get("message_id")
                    callback_id = cq.get("id")
                    username = cq.get("from", {}).get("username", "")
                    cb_data = cq.get("data", "")
                    if chat_id and cb_data:
                        handle_callback(chat_id, message_id, callback_id, username, cb_data)
                    continue

                # Regular message
                msg = upd.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                username = msg.get("from", {}).get("username", "")
                text = msg.get("text", "").strip()
                if chat_id and text:
                    handle_command(chat_id, username, text)
        except Exception as e:
            print("loop error:", e)
        time.sleep(0.3)

if __name__ == "__main__":
    main()