#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crypto Quest Telegram bot - subscription manager with inline menu
==================================================================
Polling bot (raw Bot API via urllib - works from Iran, no python-telegram-bot).
Interactive inline keyboard menu that routes customers straight to crypto payment.
All customer-facing text lives in ``lang.py``; all settings live in ``config.py``.

Commands:
  /start        - show main menu
  /subscribe    - free plan
  /premium      - premium plan (crypto payment)
  /pay <txhash> - confirm crypto payment with transaction hash
  /unsubscribe  - cancel subscription
  /status       - subscription status
  /help         - help

Architecture (each file has ONE job -> easy for a human to extend):
  config.py  - every setting, loaded from .env  (edit this to configure the bot)
  lang.py    - every customer message + button label (edit this to reword/translate)
  bot.py     - only logic + Telegram API plumbing (this file)

Runs:
  python bot.py
"""
import json
import os
import sys
import time
import datetime
import urllib.request
import urllib.parse

import config
import lang
import nowpayments   # crypto payment gateway (optional)
import channel_access  # VIP channel membership management (optional)
import admin          # owner admin panel


# ---------------------------------------------------------------------------
#  Persistence helpers
# ---------------------------------------------------------------------------
def load_subscribers():
    """Load subscriber records from disk (config.SUBSCRIBERS_FILE)."""
    if os.path.exists(config.SUBSCRIBERS_FILE):
        try:
            with open(config.SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"subscribers": []}


def save_subscribers(data):
    with open(config.SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_subscriber(data, chat_id):
    for s in data["subscribers"]:
        if str(s.get("chat_id")) == str(chat_id):
            return s
    return None


def _load_pending():
    """Pending NOWPayments invoices: chat_id -> {payment_id, product_id}."""
    if os.path.exists(config.PENDING_FILE):
        try:
            with open(config.PENDING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_pending(chat_id, value):
    """Store a pending NOWPayments record (str payment_id OR dict with product_id)."""
    data = _load_pending()
    if value == "":
        data.pop(str(chat_id), None)
    else:
        data[str(chat_id)] = value
    with open(config.PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
#  Bot API helpers (raw urllib - works from Iran)
# ---------------------------------------------------------------------------
def api_call(method, **params):
    """Call a Telegram Bot API method. Returns parsed JSON or None on error."""
    url = f"https://api.telegram.org/bot{config.TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"api error [{method}]:", e)
        return None


def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    params = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        params["reply_markup"] = json.dumps(reply_markup)
    if parse_mode:
        params["parse_mode"] = parse_mode
    return api_call("sendMessage", **params)


def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    params = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        params["reply_markup"] = json.dumps(reply_markup)
    if parse_mode:
        params["parse_mode"] = parse_mode
    return api_call("editMessageText", **params)


def answer_callback(callback_query_id, text=None):
    params = {"callback_query_id": callback_query_id}
    if text:
        params["text"] = text
    return api_call("answerCallbackQuery", **params)


def get_updates(offset):
    url = f"https://api.telegram.org/bot{config.TOKEN}/getUpdates?timeout=25&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("result", [])
    except Exception as e:
        print("getUpdates error:", e)
        return []


# ---------------------------------------------------------------------------
#  Network helpers (labels & keyboards come from lang.py)
# ---------------------------------------------------------------------------
def get_recommended_network():
    for n in config.CRYPTO_NETWORKS:
        if n.get("recommended"):
            return n
    return config.CRYPTO_NETWORKS[0]


def format_crypto_payment(product, network=None):
    """Build the full crypto payment guide for a product + network.

    The price comes from the product, so every product can have its own amount.
    """
    if network is None:
        network = get_recommended_network()
    network_line = lang.TXT["pay_network_recommended"].format(
        name=network["name"], standard=network["standard"],
    ) if network.get("recommended") else lang.TXT["pay_network"].format(
        name=network["name"], standard=network["standard"],
    )
    # If the owner hasn't set a wallet, show a warning and stop (no funds lost).
    if not config.CRYPTO_ADDRESS:
        return lang.TXT["pay_wallet_missing"]
    price = product.get("price_usd", 0.0)
    lines = [
        lang.TXT["pay_price"].format(price=price),
        "",
        network_line,
        lang.TXT["pay_token"].format(currency=network["currency"]),
        f"   {network['note']}",
        "",
        lang.TXT["pay_wallet_label"],
        f"`{config.CRYPTO_ADDRESS}`",
        "",
        lang.TXT["pay_amount"].format(price=price),
        "",
        lang.TXT["pay_after"],
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
#  Shared helpers used by several handlers
# ---------------------------------------------------------------------------
def grant_channel_access(chat_id):
    """Shared: grant VIP channel access and fold its result into a message suffix."""
    access = channel_access.grant_access(chat_id)
    suffix = ""
    if access.get("ok") and access.get("channel"):
        suffix = lang.TXT["channel_granted"].format(link=access.get("invite_link"))
    elif access.get("ok") and access.get("message"):
        suffix = lang.TXT["channel_note"].format(note=access["message"])
    return suffix


def _deliver_product(chat_id, username, product, payment_method):
    """Deliver a paid product: grant channel access OR send digital delivery.

    Returns (completed_msg, ok) where ok=True means delivery succeeded.
    Sets/updates the subscriber's paid access record for status tracking.
    """
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    kind = product.get("kind", "channel")
    days = product.get("days", 0)

    # Update paid-access record on the subscriber (for /status + sweep).
    if not sub:
        data["subscribers"].append({
            "chat_id": str(chat_id), "username": username or "",
            "plan": "premium", "subscribed_at": datetime.datetime.now().isoformat(),
            "premium_until": _expiry(days), "payment_method": payment_method,
            "product_id": product.get("id"),
        })
    else:
        sub["plan"] = "premium"
        sub["premium_until"] = _expiry(days)
        sub["payment_method"] = payment_method
        sub["product_id"] = product.get("id")
    save_subscribers(data)

    if kind == "digital":
        deliver_text = product.get("deliver") or product.get("description", product["name"])
        return lang.TXT["pay_received_digital"].format(
            tx="(nowpayments)" if payment_method == "nowpayments" else "(crypto)",
            deliver=deliver_text,
        ), True

    # Channel delivery
    msg = lang.TXT["pay_received_channel"].format(
        tx="(nowpayments)" if payment_method == "nowpayments" else "(crypto)",
        days=days if days else 0,
    )
    suffix = grant_channel_access(chat_id)
    if suffix:
        msg += suffix
    else:
        msg += lang.TXT["pay_awaiting_confirm"]
    return msg, True


def _expiry(days):
    """ISO expiry for a grant of N days (0 days -> 1 year lifetime placeholder)."""
    if days and days > 0:
        return (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    return (datetime.datetime.now() + datetime.timedelta(days=3650)).isoformat()


# ---------------------------------------------------------------------------
#  Keyboard builders (button labels all come from lang)
# ---------------------------------------------------------------------------
def network_keyboard(product_id=None):
    """Payment network keyboard. If a product is being bought, back goes to the shop."""
    rows = []
    for n in config.CRYPTO_NETWORKS:
        cb = lang.network_callback(n)
        if product_id:
            cb = f"{cb}:{product_id}"
        rows.append([
            {"text": lang.network_button(n), "callback_data": cb}
        ])
    if product_id:
        rows.append([{"text": lang.BTN["pay_nowpayments"], "callback_data": f"pay_nowpayments:{product_id}"}])
    else:
        rows.append([{"text": lang.BTN["pay_nowpayments"], "callback_data": "pay_nowpayments"}])
    if product_id:
        rows.append([{"text": lang.BTN["back_shop"], "callback_data": "shop"}])
    rows.append([{"text": lang.BTN["back_menu"], "callback_data": "menu"}])
    return {"inline_keyboard": rows}


def shop_keyboard():
    """Main shop keyboard: one button per product in config.PRODUCTS."""
    rows = []
    for p in config.PRODUCTS:
        rows.append([
            {"text": lang.product_button(p), "callback_data": lang.product_callback(p)}
        ])
    rows.append([{"text": lang.BTN["back_menu"], "callback_data": "menu"}])
    return {"inline_keyboard": rows}


def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["shop"], "callback_data": "shop"}],
            [{"text": lang.BTN["free_sub"], "callback_data": "sub_free"}],
            [{"text": lang.BTN["status"], "callback_data": "status"}],
            [{"text": lang.BTN["help"], "callback_data": "help"}],
            [{"text": lang.BTN["unsubscribe"], "callback_data": "unsubscribe"}],
        ]
    }


def pay_done_keyboard():
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["pay_done"], "callback_data": "pay_done"}],
            [{"text": lang.BTN["back_menu"], "callback_data": "menu"}],
        ]
    }


def back_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["back_menu"], "callback_data": "menu"}],
        ]
    }


def pay_check_keyboard():
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["check_payment"], "callback_data": "check_payment"}],
            [{"text": lang.BTN["back_menu"], "callback_data": "menu"}],
        ]
    }


# ---------------------------------------------------------------------------
#  Handlers
# ---------------------------------------------------------------------------
def show_main_menu(chat_id, message_id=None):
    text = lang.TXT["welcome"]
    if message_id is not None:
        return edit_message(chat_id, message_id, text, main_menu_keyboard())
    return send_message(chat_id, text, main_menu_keyboard())


def handle_subscribe(chat_id, username, data):
    if find_subscriber(data, chat_id):
        return send_message(chat_id, lang.TXT["already_subscribed"], back_menu_keyboard())
    data["subscribers"].append({
        "chat_id": str(chat_id),
        "username": username or "",
        "plan": "free",
        "subscribed_at": datetime.datetime.now().isoformat(),
        "premium_until": None,
        "payment_method": None,
    })
    save_subscribers(data)
    return send_message(chat_id, lang.TXT["free_activated"], back_menu_keyboard())


def handle_shop(chat_id, message_id=None):
    """Show the list of products (shop)."""
    text = lang.TXT["shop_title"]
    if message_id is not None:
        return edit_message(chat_id, message_id, text, shop_keyboard())
    return send_message(chat_id, text, shop_keyboard())


def handle_product(chat_id, message_id, product_id):
    """Show a product's payment page and the network keyboard."""
    product = config.get_product(product_id)
    if product is None:
        return edit_message(chat_id, message_id, lang.TXT["product_sold_out"], shop_keyboard())
    price = product.get("price_usd", 0.0)
    text = lang.TXT["product_page"].format(
        emoji=product.get("emoji", lang.TXT["emoji_default"]),
        name=product["name"],
        description=product.get("description", ""),
        price=price,
        duration=lang.product_duration(product),
    )
    return edit_message(chat_id, message_id, text, network_keyboard(product_id))


def handle_premium(chat_id, message_id=None):
    """Legacy guard: route straight into the shop (first product if only one)."""
    handle_shop(chat_id, message_id)


def handle_pay_network(chat_id, message_id, network_name, product_id=None):
    network = next(
        (n for n in config.CRYPTO_NETWORKS if n["name"].lower() == network_name),
        None,
    )
    if network is None:
        network = get_recommended_network()
    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        return edit_message(chat_id, message_id, lang.TXT["product_sold_out"], shop_keyboard())
    text = format_crypto_payment(product, network)
    # Remember which product is being paid so "I paid" + tx-hash delivers it.
    _save_pending(chat_id, {"action": "pay", "product_id": product.get("id")})
    return edit_message(chat_id, message_id, text, pay_done_keyboard(), parse_mode="Markdown")


def handle_pay_done(chat_id, message_id):
    return edit_message(chat_id, message_id, lang.TXT["pay_howto"], back_menu_keyboard())


def handle_nowpayments(chat_id, message_id, product_id=None):
    """Create a NOWPayments invoice so the customer pays to the owner's account."""
    if not nowpayments.is_configured():
        kb = network_keyboard(product_id) if product_id else shop_keyboard()
        return edit_message(chat_id, message_id, lang.TXT["np_coming_soon"], kb)

    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        return edit_message(chat_id, message_id, lang.TXT["product_sold_out"], shop_keyboard())

    price = product.get("price_usd", 0.0)
    payment = nowpayments.create_payment(
        price_usd=price,
        pay_currency=config.NOWPAYMENTS_DEFAULT_CURRENCY,
        order_id=f"cq-{chat_id}-{int(time.time())}",
        description=f"{product['name']} - {product.get('days', 0)} days",
    )
    text = nowpayments.format_payment_instructions(payment)
    if "Invoice" in text:
        # Store pending + which product it's for.
        _save_pending(chat_id, {
            "payment_id": payment.get("payment_id"),
            "product_id": product.get("id"),
        })
        return edit_message(chat_id, message_id, text, pay_check_keyboard(), parse_mode="Markdown")
    return edit_message(chat_id, message_id, text, back_menu_keyboard())


def _finalize_paid_payment(chat_id, payment_id, product_id=None):
    """Deliver a confirmed NOWPayments payment and clear it from pending.

    Returns the confirmation message, or None if nothing to do.
    Shared by the manual "Check payment status" button AND the background
    auto-poll, so a paid invoice is delivered exactly once.
    """
    pending = _load_pending().get(str(chat_id))
    if not pending:
        return None
    pending_pid = pending.get("payment_id") if isinstance(pending, dict) else pending
    # Only finalize if this is the current pending invoice, and caller agrees.
    if product_id is None:
        product_id = pending.get("product_id") if isinstance(pending, dict) else None

    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        product = config.get_default_product() or {
            "id": None, "name": "item", "days": config.PREMIUM_DAYS, "kind": "channel"}
    days = product.get("days") or config.PREMIUM_DAYS
    # load subscriber username (may be blank for auto-poll; acceptable)
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    username = (sub or {}).get("username", "")

    msg, _ = _deliver_product(chat_id, username, product, "nowpayments")
    _save_pending(chat_id, "")  # clear pending so we never double-deliver
    if product.get("kind") == "channel":
        msg = lang.TXT["np_payment_confirmed"].format(days=days) + \
            ("\n" + msg if msg else "")
    return msg


def handle_check_payment(chat_id, username, message_id):
    """Check the status of the customer's pending NOWPayments invoice."""
    pending = _load_pending().get(str(chat_id))
    if not pending:
        text = lang.TXT["np_no_pending"]
        return edit_message(chat_id, message_id, text, shop_keyboard())

    payment_id = pending.get("payment_id") if isinstance(pending, dict) else pending
    product_id = pending.get("product_id") if isinstance(pending, dict) else None

    status = nowpayments.get_payment_status(payment_id)
    state = status.get("payment_status", "unknown") if isinstance(status, dict) else "unknown"

    if state == "finished":
        msg = _finalize_paid_payment(chat_id, payment_id, product_id)
        if msg is None:
            msg = lang.TXT["np_error"]
        return edit_message(chat_id, message_id, msg, back_menu_keyboard())

    if state in ("waiting", "confirming", "partially_paid", "expired"):
        text = lang.TXT["np_waiting"].format(state=state)
        return edit_message(chat_id, message_id, text, pay_check_keyboard(), parse_mode="Markdown")

    return edit_message(chat_id, message_id, lang.TXT["np_error"], pay_check_keyboard())


def poll_pending_payments():
    """Background auto-poll of pending NOWPayments invoices (like IPN, no server).

    Called periodically from the main loop. For each pending payment it asks
    NOWPayments for the current status; if a payment became ``finished`` it
    delivers the product automatically and messages the customer — no manual
    "Check payment status" tap needed.
    """
    pendings = _load_pending()
    if not pendings:
        return 0
    delivered = 0
    for chat_id, pending in list(pendings.items()):
        if not pending or pending == "":
            continue
        payment_id = pending.get("payment_id") if isinstance(pending, dict) else pending
        if not payment_id:
            continue
        status = nowpayments.get_payment_status(payment_id)
        state = status.get("payment_status", "unknown") if isinstance(status, dict) else "unknown"
        if state != "finished":
            continue
        product_id = pending.get("product_id") if isinstance(pending, dict) else None
        msg = _finalize_paid_payment(chat_id, payment_id, product_id)
        if msg:
            send_message(chat_id, msg, back_menu_keyboard())
            delivered += 1
            print(f"   [auto] delivered paid invoice for chat {chat_id}")
    return delivered


def handle_status(chat_id, message_id=None):
    sub = find_subscriber(load_subscribers(), chat_id)
    if not sub:
        text = lang.TXT["not_subscribed"]
    else:
        # Show which product they have access to, if known.
        product_name = ""
        if sub.get("product_id"):
            p = config.get_product(sub["product_id"])
            product_name = (p or {}).get("name", sub["product_id"])
        plan = lang.TXT["plan_premium"] if sub.get("plan") == "premium" else lang.TXT["plan_free"]
        text = lang.TXT["status"].format(
            plan=(plan + (f" ({product_name})" if product_name else "")),
            since=sub.get("subscribed_at", "—")[:10],
            until=sub.get("premium_until", "—"),
        )
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())


def handle_help(chat_id, message_id=None):
    text = lang.TXT["help"]
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())


def handle_unsubscribe(chat_id, message_id=None):
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    if sub:
        data["subscribers"] = [s for s in data["subscribers"] if str(s.get("chat_id")) != str(chat_id)]
        save_subscribers(data)
        channel_access.revoke_access(chat_id)  # remove from VIP channel if configured
        text = lang.TXT["unsubscribed"]
    else:
        text = lang.TXT["not_subscribed_2"]
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())


def handle_pay(chat_id, username, txhash):
    """Manual /pay <txhash> handler (or free-text hash after "I paid").

    Delivers the product the user selected in the shop (stored in pending),
    or the default/first product if none was selected. Clears the pending
    "pay" marker so we don't re-deliver on a second message.
    """
    pending = _load_pending().get(str(chat_id))
    product_id = pending.get("product_id") if isinstance(pending, dict) else None
    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        return send_message(chat_id, lang.TXT["product_sold_out"], back_menu_keyboard())
    msg, _ = _deliver_product(chat_id, username, product, "crypto")
    msg = msg.replace("(crypto)", txhash[:20] + "...", 1)
    _save_pending(chat_id, "")  # clear the pending "pay" marker
    return send_message(chat_id, msg, back_menu_keyboard())


# ---------------------------------------------------------------------------
#  Callback + admin command dispatch
# ---------------------------------------------------------------------------
def handle_callback(chat_id, message_id, callback_id, username, cb_data):
    answer_callback(callback_id)  # acknowledge silently (no popup/checkmark)

    if cb_data == "menu":
        show_main_menu(chat_id, message_id)
    elif cb_data == "sub_free":
        handle_subscribe(chat_id, username, load_subscribers())
    elif cb_data == "shop":
        handle_shop(chat_id, message_id)
    elif cb_data == "premium":
        handle_premium(chat_id, message_id)
    elif cb_data.startswith("prod_"):
        # Select a product -> show its payment page + network keyboard.
        handle_product(chat_id, message_id, cb_data[len("prod_"):])
    elif cb_data.startswith("pay_"):
        # Network selected for a product. Format: pay_bsc / pay_bsc:prod_id
        payload = cb_data[len("pay_"):]
        if ":" in payload:
            network_name, product_id = payload.split(":", 1)
        else:
            network_name, product_id = payload, None
        handle_pay_network(chat_id, message_id, network_name, product_id)
    elif cb_data == "pay_nowpayments" or cb_data.startswith("pay_nowpayments:"):
        product_id = None
        if ":" in cb_data:
            product_id = cb_data.split(":", 1)[1]
        handle_nowpayments(chat_id, message_id, product_id)
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


def handle_admin_command(chat_id, command):
    """Owner-only commands (stats, broadcast, add/kick member, set price)."""
    if not admin.is_owner(chat_id):
        return False

    cmd = command.strip()

    if cmd == "/stats":
        data = load_subscribers()
        subs = data.get("subscribers", [])
        premium = len([s for s in subs if s.get("plan") == "premium"])
        free = len([s for s in subs if s.get("plan") == "free"])
        text = lang.TXT["admin_stats"].format(
            total=len(subs), premium=premium, free=free,
            revenue=premium * config.PRICE_USD,
        )
        send_message(chat_id, text, back_menu_keyboard())
        return True

    elif cmd == "/products":
        lines = [lang.TXT["products_title"], ""]
        for p in config.PRODUCTS:
            lines.append(lang.TXT["products_line"].format(
                emoji=p.get("emoji", lang.TXT["emoji_default"]), name=p["name"],
                price=p.get("price_usd", 0), duration=lang.product_duration(p),
                kind=p.get("kind", "channel"),
            ))
        send_message(chat_id, "\n".join(lines), back_menu_keyboard())
        return True

    elif cmd == "/admin":
        text = lang.TXT["admin_help"].format(days=config.PREMIUM_DAYS)
        send_message(chat_id, text, back_menu_keyboard())
        return True

    elif cmd.startswith("/broadcast "):
        msg = cmd.split(" ", 1)[1].strip()
        data = load_subscribers()
        sent, failed = 0, 0
        for s in data.get("subscribers", []):
            cid = s.get("chat_id")
            if cid:
                if send_message(cid, lang.TXT["broadcast_msg"].format(msg=msg)):
                    sent += 1
                else:
                    failed += 1
        text = lang.TXT["broadcast_sent"].format(sent=sent)
        if failed:
            text += lang.TXT["broadcast_partial"].format(failed=failed)
        send_message(chat_id, text, back_menu_keyboard())
        return True

    elif cmd.startswith("/add_member "):
        user_id = cmd.split(" ", 1)[1].strip()
        if not user_id.lstrip("-").isdigit():
            send_message(chat_id, lang.TXT["invalid_user_id"], back_menu_keyboard())
            return True
        err = admin.add_premium_member(config.SUBSCRIBERS_FILE, user_id, days=config.PREMIUM_DAYS)
        if err:
            send_message(chat_id, f"❌ {err}", back_menu_keyboard())
        else:
            suffix = grant_channel_access(user_id)
            text = lang.TXT["member_granted"].format(uid=user_id, days=config.PREMIUM_DAYS)
            if suffix:
                text += lang.TXT["member_granted_channel"].format(link=suffix)
            send_message(chat_id, text, back_menu_keyboard())
        return True

    elif cmd.startswith("/kick "):
        user_id = cmd.split(" ", 1)[1].strip()
        removed = admin.remove_member(config.SUBSCRIBERS_FILE, user_id)
        channel_access.revoke_access(user_id)
        text = (lang.TXT["member_removed"].format(uid=user_id) if removed
                else lang.TXT["member_not_found"].format(uid=user_id))
        send_message(chat_id, text, back_menu_keyboard())
        return True

    elif cmd.startswith("/set_price "):
        try:
            new_price = float(cmd.split(" ", 1)[1].strip())
            if new_price <= 0:
                raise ValueError
        except ValueError:
            send_message(chat_id, lang.TXT["invalid_price"], back_menu_keyboard())
            return True
        config.PRICE_USD = new_price  # in-memory for this run
        send_message(chat_id, lang.TXT["price_updated"].format(price=new_price), back_menu_keyboard())
        return True

    return False


def handle_command(chat_id, username, command):
    if handle_admin_command(chat_id, command):
        return
    data = load_subscribers()

    if command == "/start":
        show_main_menu(chat_id)
    elif command == "/subscribe":
        handle_subscribe(chat_id, username, data)
    elif command in ("/shop", "/premium"):
        handle_shop(chat_id) if command == "/shop" else handle_premium(chat_id)
    elif command.startswith("/pay "):
        handle_pay(chat_id, username, command.split(" ", 1)[1].strip())
    elif command == "/unsubscribe":
        handle_unsubscribe(chat_id)
    elif command == "/status":
        handle_status(chat_id)
    elif command == "/help":
        handle_help(chat_id)
    elif not command.startswith("/"):
        # Not a slash command -> if the user is mid-payment (selected a network
        # and tapped "I paid"), treat this free-text as a transaction hash.
        pending = _load_pending().get(str(chat_id))
        if isinstance(pending, dict) and pending.get("product_id") and command.strip():
            handle_pay(chat_id, username, command.strip())
            return
        send_message(chat_id, lang.TXT["unknown_command"], main_menu_keyboard())
    else:
        send_message(chat_id, lang.TXT["unknown_command"], main_menu_keyboard())


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------
_last_sweep = 0.0
_last_payment_poll = 0.0
_PAYMENT_POLL_INTERVAL = 20.0   # check pending payments every 20 seconds


def main():
    global _last_sweep, _last_payment_poll
    if not config.TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    print("✅ Bot running... (polling with inline menu + auto payment-poll)")
    if nowpayments.is_configured():
        print(f"   Auto-delivery: checking pending NOWPayments every {_PAYMENT_POLL_INTERVAL:.0f}s")
    else:
        print("   Auto-delivery: OFF (NOWPayments not configured)")

    # Drain stale updates so we don't reply to expired callbacks (fixes 400).
    offset = 0
    for upd in get_updates(offset):
        offset = max(offset, upd.get("update_id", 0) + 1)

    while True:
        try:
            for upd in get_updates(offset):
                update_id = upd.get("update_id", 0)
                offset = update_id + 1

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

                msg = upd.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                username = msg.get("from", {}).get("username", "")
                text = msg.get("text", "").strip()
                if chat_id and text:
                    handle_command(chat_id, username, text)
        except Exception as e:
            print("loop error:", e)

        # Periodically sweep expired premium memberships.
        try:
            if time.time() - _last_sweep >= config.SWEEP_INTERVAL_SECONDS:
                kicked = channel_access.check_expired(config.SUBSCRIBERS_FILE)
                if kicked:
                    print(f"   Sweep: removed {len(kicked)} expired member(s)")
                _last_sweep = time.time()
        except Exception as e:
            print("sweep error:", e)

        # Auto-deliver confirmed payments (background "IPN"-like check).
        try:
            if nowpayments.is_configured() and \
               time.time() - _last_payment_poll >= _PAYMENT_POLL_INTERVAL:
                poll_pending_payments()
                _last_payment_poll = time.time()
        except Exception as e:
            print("payment-poll error:", e)
        time.sleep(0.3)


if __name__ == "__main__":
    main()
