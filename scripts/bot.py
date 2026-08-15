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
import threading
import time
import datetime
import urllib.request
import urllib.parse

import config
# Force IPv4 for all outbound HTTP(S) to Telegram. This server's IPv6 route
# to Telegram is slow/unstable; using IPv4 makes polling reliable and fast.
import socket as _socket
_orig_getaddrinfo = _socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0, **kw):
    # Force IPv4 for all outbound connections (family=AF_INET).
    if family == _socket.AF_UNSPEC:
        family = _socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags, **kw)
_socket.getaddrinfo = _ipv4_getaddrinfo


import lang
import nowpayments   # crypto payment gateway (optional)
import coingate      # web-payment gateway, optional 2nd option
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
#  Add-product wizard (step-by-step, owner only)
#  ---------------------------------------------------------------------------
#  Instead of a long one-line command, the owner taps "Add Product" and the
#  bot asks one field at a time: name, price, days, kind, discount. The owner
#  may skip any field by sending an empty/blank reply — that field is simply
#  not set (or gets a sensible default). Field values fail validation, the
#  step is repeated; on "cancel" the whole thing is abandoned.
_WIZARD_STEPS = ["category", "name", "model", "price", "days", "discount"]

def _load_wizard():
    try:
        if os.path.exists(config.WIZARD_FILE):
            with open(config.WIZARD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_wizard_state(chat_id, state):
    data = _load_wizard()
    if state is None:
        data.pop(str(chat_id), None)
    else:
        data[str(chat_id)] = state
    with open(config.WIZARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return state

def wizard_step_message(chat_id=None):
    """Return (text, ok) for the current wizard step, or (None, False) if idle."""
    st = _load_wizard().get(str(chat_id)) if chat_id is not None else None
    if not st or not st.get("active"):
        return None, False
    step = st.get("step")
    if step == "category":
        return lang.TXT["wiz_category"], True
    if step == "name":
        return lang.TXT["wiz_name"], True
    if step == "model":
        return lang.TXT["wiz_model"], True
    if step == "price":
        return lang.TXT["wiz_price"], True
    if step == "days":
        return lang.TXT["wiz_days"], True
    if step == "discount":
        return lang.TXT["wiz_discount"], True
    return None, False

def start_add_product_wizard(chat_id, message_id=None):
    """Begin the stepped add-product flow: ask for the product name."""
    _save_wizard_state(chat_id, {"active": True, "step": "category", "data": {}})
    text, _ = wizard_step_message(chat_id)
    if message_id is not None:
        return edit_message(chat_id, message_id, text, wizard_keyboard())
    return send_message(chat_id, text, wizard_keyboard())

def wizard_keyboard():
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["wizard_back"], "callback_data": "wizard_back"},
             {"text": lang.BTN["wizard_skip"], "callback_data": "wizard_skip"},
             {"text": lang.BTN["wizard_cancel"], "callback_data": "wizard_cancel"}],
        ]
    }

def _finish_wizard_product(chat_id):
    """Build + save the product from accumulated wizard data, then confirm."""
    st = _load_wizard().get(str(chat_id), {})
    d = st.get("data", {})
    name = (d.get("name") or "").strip()
    price = d.get("price")
    if not name or price is None:
        return send_message(chat_id, lang.TXT["wiz_incomplete"], main_menu_keyboard(chat_id))
    pid = name.lower().replace(" ", "_")[:20]
    new_id = pid
    n = 1
    while config.get_product(new_id):
        new_id = f"{pid}_{n}"; n += 1
    days = d.get("days")
    category = (d.get("category") or "channel").lower()
    discount = d.get("discount", 0) or 0
    product = {
        "id": new_id, "name": name, "price_usd": price,
        "days": days if days is not None else config.PREMIUM_DAYS,
        "kind": d.get("model", ""),
        "category": category,
        "description": f"{name} — access to {name}.",
    }
    if discount:
        product["discount"] = discount
    if d.get("model", "") == "digital":
        product["deliver"] = ""
    config.PRODUCTS.append(product)
    config.save_products()
    _save_wizard_state(chat_id, None)  # clear wizard
    disc_note = f" (-{discount:.0f}%)" if discount else ""
    return send_message(
        chat_id,
        lang.TXT["prod_added"].format(name=name, price=config.effective_price(product),
                                       days=product["days"], kind=category, disc=disc_note),
        owner_keyboard())

def _advance_wizard(chat_id, value):
    """Process one wizard reply (value may be '' to skip). Returns (text, done)."""
    st = _load_wizard().get(str(chat_id))
    if not st or not st.get("active"):
        return None, False
    step = st.get("step")
    d = st.get("data", {})
    val = value.strip()

    if step == "category":
        if val:
            d["category"] = val.strip()
    elif step == "name":
        if val:
            d["name"] = val
    elif step == "model":
        if val:
            d["model"] = val.strip()
    elif step == "price":
        if val:
            try:
                p = float(val)
                if p <= 0:
                    return lang.TXT["wiz_invalid_price"].format(hint=val), False
                d["price"] = p
            except ValueError:
                return lang.TXT["wiz_invalid_price"].format(hint=val), False
        # price is required to finish; if skipped, remain on this step
        if "price" not in d:
            return lang.TXT["wiz_price"], False
    elif step == "days":
        if val:
            try:
                d["days"] = max(int(float(val)), 0)
            except ValueError:
                return lang.TXT["wiz_invalid_days"].format(hint=val), False
    elif step == "discount":
        if val:
            try:
                disc = float(val)
                if disc < 0 or disc >= 100:
                    return lang.TXT["wiz_invalid_discount"].format(hint=val), False
                d["discount"] = disc
            except ValueError:
                return lang.TXT["wiz_invalid_discount"].format(hint=val), False

    # advance
    idx = _WIZARD_STEPS.index(step)
    if idx + 1 < len(_WIZARD_STEPS):
        next_step = _WIZARD_STEPS[idx + 1]
        st["step"] = next_step
        st["data"] = d
        _save_wizard_state(chat_id, st)
        text, _ = wizard_step_message(chat_id)
        return text, False
    # all steps done -> persist the final data, then finalize
    st["data"] = d
    _save_wizard_state(chat_id, st)
    _finish_wizard_product(chat_id)
    return None, True


def _wizard_back(chat_id):
    """Go back one step in the add-product wizard."""
    st = _load_wizard().get(str(chat_id))
    if not st or not st.get("active"):
        return None, False
    step = st.get("step")
    idx = _WIZARD_STEPS.index(step)
    if idx <= 0:
        return None, False  # already at first step
    prev_step = _WIZARD_STEPS[idx - 1]
    st["step"] = prev_step
    _save_wizard_state(chat_id, st)
    text, _ = wizard_step_message(chat_id)
    return text, True


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
    res = api_call("sendMessage", **params)
    print(f"[send] -> {chat_id}: {text[:50]} | ok={bool(res)}")
    return res


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
    _t0 = time.time()
    url = f"https://api.telegram.org/bot{config.TOKEN}/getUpdates?timeout=25&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=28) as resp:
            result = json.loads(resp.read().decode()).get("result", [])
            _dt = time.time() - _t0
            if result:
                detail = []
                for u in result:
                    cq = u.get('callback_query')
                    if cq:
                        detail.append(f"{u.get('update_id')}=cb:{cq.get('data','')[:25]}")
                    else:
                        m = u.get('message', {})
                        detail.append(f"{u.get('update_id')}=msg:{m.get('text','(none)')[:20]}")
                print(f"[updates] got {len(result)} in {_dt:.1f}s: " + ', '.join(detail))
            return result
    except Exception as e:
        print(f"getUpdates error after {time.time()-_t0:.1f}s:", e)
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
    price = config.effective_price(product)
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


def _notify_owner_sale(chat_id, username, product, payment_method):
    """Notify the owner (OWNER_CHAT_ID) when a product is sold & delivered."""
    owner = config.OWNER_CHAT_ID
    if not owner:
        return
    buyer = username or str(chat_id)
    method = payment_method if payment_method else "crypto"
    text = lang.TXT["sale_notification"].format(
        name=product.get("name", "item"),
        price=config.effective_price(product),
        user=buyer,
        method=method,
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    send_message(owner, text)


def _deliver_product(chat_id, username, product, payment_method):
    """Deliver a paid product: grant channel access OR send digital delivery.

    Returns (completed_msg, ok) where ok=True means delivery succeeded.
    Sets/updates the subscriber's paid access record for status tracking.
    Also notifies the owner of the sale.
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

    # Notify the owner that a sale happened (only on confirmed delivery).
    _notify_owner_sale(chat_id, username, product, payment_method)

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
    # Payment gateways (only shown if configured)
    if product_id:
        if config.NOWPAYMENTS_API_KEY:
            rows.append([{"text": lang.BTN["pay_nowpayments"], "callback_data": f"pay_nowpayments:{product_id}"}])
        if coingate.is_configured():
            rows.append([{"text": lang.BTN["pay_coingate"], "callback_data": f"pay_coingate:{product_id}"}])
        rows.append([{"text": lang.BTN["back_shop"], "callback_data": "shop"}])
    else:
        if config.NOWPAYMENTS_API_KEY:
            rows.append([{"text": lang.BTN["pay_nowpayments"], "callback_data": "pay_nowpayments"}])
        if coingate.is_configured():
            rows.append([{"text": lang.BTN["pay_coingate"], "callback_data": "pay_coingate"}])
    rows.append([{"text": lang.BTN["back_menu"], "callback_data": "menu"}])
    return {"inline_keyboard": rows}


def shop_keyboard():
    """Shop keyboard: show category buttons first, then products per category.
    This keeps the menu clean even as the catalogue grows into dozens of items.
    """
    # Collect unique categories from all products
    cats = {}
    for p in config.PRODUCTS:
        cat = p.get("category") or p.get("kind", "other")
        if cat not in cats:
            header_key = {"channel": "cat_channel", "digital": "cat_digital"}.get(cat, "cat_other")
            cats[cat] = lang.TXT[header_key]
    rows = []
    for cat, label in cats.items():
        rows.append([{"text": label, "callback_data": f"cat_{cat}"}])
    rows.append([{"text": lang.BTN["back_menu"], "callback_data": "menu"}])
    return {"inline_keyboard": rows}


def category_keyboard(category):
    """Products within a single category."""
    rows = []
    for p in config.PRODUCTS:
        pcat = p.get("category") or p.get("kind", "other")
        if pcat == category:
            rows.append([
                {"text": lang.product_button(p), "callback_data": lang.product_callback(p)}
            ])
    rows.append([{"text": lang.BTN["back_shop"], "callback_data": "shop"}])
    return {"inline_keyboard": rows}


def main_menu_keyboard(chat_id=None):
    """Main menu. Built from config.MENU_ITEMS (all buttons shown)."""
    rows = []
    for key, item in config.MENU_ITEMS.items():
        rows.append([
            {"text": lang.BTN[item["label_key"]], "callback_data": item["btn"]}
        ])
    # Owner-only management button (private to the owner).
    if chat_id is not None and admin.is_owner(chat_id):
        rows.append([{"text": lang.BTN["owner_manage"], "callback_data": "owner_manage"}])
    return {"inline_keyboard": rows}


def owner_keyboard():
    """Owner menu: product management actions (owner only)."""
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["owner_add_product"], "callback_data": "owner_add_product"}],
            [{"text": lang.BTN["owner_remove_product"], "callback_data": "owner_remove_product"}],
            [{"text": lang.BTN["owner_list_products"], "callback_data": "owner_list_products"}],
            [{"text": lang.BTN["owner_howto_add"], "callback_data": "owner_howto_add"}],
            [{"text": lang.BTN["back_menu"], "callback_data": "menu"}],
        ]
    }


def remove_product_keyboard():
    """Owner: list products, each as a button to remove."""
    rows = []
    for p in config.PRODUCTS:
        rows.append([
            {"text": f"{p.get('emoji', lang.TXT['emoji_default'])} {p['name']} — ${config.effective_price(p):.2f}",
             "callback_data": f"rm_prod:{p['id']}"}
        ])
    rows.append([{"text": lang.BTN["owner_manage"], "callback_data": "owner_manage"}])
    rows.append([{"text": lang.BTN["back_menu"], "callback_data": "menu"}])
    return {"inline_keyboard": rows}


def confirm_remove_keyboard(product_id):
    """Owner: confirm before removing a product."""
    return {
        "inline_keyboard": [
            [{"text": lang.BTN["owner_confirm_yes"], "callback_data": f"rm_confirm:{product_id}"}],
            [{"text": lang.BTN["owner_confirm_no"], "callback_data": "owner_remove_product"}],
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


def pay_check_keyboard(invoice_url=None):
    """Keyboard after an invoice is created. If we have a payment page URL,
    show a button that opens it directly (inline URL), plus Check status."""
    rows = []
    if invoice_url:
        rows.append([{"text": lang.BTN["open_payment"], "url": invoice_url}])
    rows.append([{"text": lang.BTN["check_payment"], "callback_data": "check_payment"}])
    rows.append([{"text": lang.BTN["back_menu"], "callback_data": "menu"}])
    return {"inline_keyboard": rows}


# ---------------------------------------------------------------------------
#  Handlers
# ---------------------------------------------------------------------------
def show_main_menu(chat_id, message_id=None):
    text = lang.TXT["welcome"]
    if message_id is not None:
        return edit_message(chat_id, message_id, text, main_menu_keyboard(chat_id))
    return send_message(chat_id, text, main_menu_keyboard(chat_id))


def handle_subscribe(chat_id, username, data):
    """Subscription: join the owner's channel (or contact support if unconfigured)."""
    # Always record the membership so the account page shows a join date.
    if not find_subscriber(data, chat_id):
        data["subscribers"].append({
            "chat_id": str(chat_id),
            "username": username or "",
            "plan": "free",
            "subscribed_at": datetime.datetime.now().isoformat(),
            "premium_until": None,
            "payment_method": None,
        })
        save_subscribers(data)
    # Send the owner's channel invite link, if one is configured.
    if config.CHANNEL_LINK:
        return send_message(chat_id, lang.TXT["subscription_join"].format(link=config.CHANNEL_LINK), back_menu_keyboard())
    if config.SUPPORT_URL:
        return send_message(chat_id, lang.TXT["subscription_contact_support"].format(link=config.SUPPORT_URL), back_menu_keyboard())
    return send_message(chat_id, lang.TXT["subscription_not_ready"], back_menu_keyboard())


def handle_shop(chat_id, message_id=None):
    """Show the list of products (shop)."""
    text = lang.TXT["shop_title"]
    if message_id is not None:
        return edit_message(chat_id, message_id, text, shop_keyboard())
    return send_message(chat_id, text, shop_keyboard())


def _owner_list(chat_id, message_id):
    """Owner-only: show all products with ids (to manage them)."""
    lines = [lang.TXT["products_title"], ""]
    for p in config.PRODUCTS:
        lines.append(lang.TXT["products_line"].format(
            emoji=p.get("emoji", lang.TXT["emoji_default"]), name=p["name"],
            price=config.effective_price(p), duration=lang.product_duration(p),
            kind=p.get("kind", "channel"),
        ))
    lines.append("")
    lines.append("Use /remove_product <id> to delete one.")
    edit_message(chat_id, message_id, "\n".join(lines), owner_keyboard())


def handle_product(chat_id, message_id, product_id):
    """Show a product's payment page and the network keyboard."""
    product = config.get_product(product_id)
    if product is None:
        return edit_message(chat_id, message_id, lang.TXT["product_sold_out"], shop_keyboard())
    price = config.effective_price(product)
    disc = product.get("discount", 0) or 0
    if disc:
        # Original (discount% off) = discounted
        price_line = lang.TXT["price_discounted"].format(
            orig=float(product.get("price_usd", price)), discount=disc, price=price)
    else:
        price_line = lang.TXT["price_normal"].format(price=price)
    text = lang.TXT["product_page"].format(
        emoji=product.get("emoji", lang.TXT["emoji_default"]),
        name=product["name"],
        description=product.get("description", ""),
        price_line=price_line,
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
    """After the customer taps 'I paid' for a MANUAL crypto payment, ask them
    to send the transaction hash (TXID). NOWPayments uses check_payment instead
    so it never enters this free-text flow."""
    # Determine payment type from pending.
    pending = _load_pending().get(str(chat_id))
    is_np = bool(pending) and isinstance(pending, dict) and pending.get("payment_id")
    if is_np:
        # NOWPayments: no free-text TXID needed — ask to check status.
        return edit_message(chat_id, message_id, lang.TXT["np_check_status"], pay_check_keyboard())
    # Manual crypto payment -> ask for the transaction hash.
    _save_pending(chat_id, {"action": "await_txid", "product_id": pending.get("product_id") if isinstance(pending, dict) else None})
    return edit_message(chat_id, message_id, lang.TXT["send_txid"] + "\n\n" + lang.TXT["send_txid_hint"], back_menu_keyboard())



def handle_nowpayments(chat_id, message_id, product_id=None):
    """Create a NOWPayments invoice so the customer pays to the owner's account."""
    if not nowpayments.is_configured():
        kb = network_keyboard(product_id) if product_id else shop_keyboard()
        return edit_message(chat_id, message_id, lang.TXT["np_coming_soon"], kb)

    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        return edit_message(chat_id, message_id, lang.TXT["product_sold_out"], shop_keyboard())

    price = config.effective_price(product)
    # Create a hosted invoice (payment page) so the customer gets a clickable
    # link to pay with card or crypto — no manual address/amount entry needed.
    invoice = nowpayments.create_invoice(
        price_usd=price,
        pay_currency=config.NOWPAYMENTS_DEFAULT_CURRENCY,
        order_id=f"cq-{chat_id}-{int(time.time())}",
        description=f"{product['name']} - {product.get('days', 0)} days",
    )
    invoice_url = invoice.get("invoice_url") if isinstance(invoice, dict) else None
    if invoice_url:
        # Customer opens the link to pay, then clicks "I paid" back here.
        text = nowpayments.format_invoice_instructions(invoice, product)
        _save_pending(chat_id, {
            "payment_id": invoice.get("id"),
            "product_id": product.get("id"),
        })
        return edit_message(chat_id, message_id, text, pay_check_keyboard(invoice_url), parse_mode="Markdown")
    # Fallback: old-style payment (address/amount)
    payment = nowpayments.create_payment(
        price_usd=price,
        pay_currency=config.NOWPAYMENTS_DEFAULT_CURRENCY,
        order_id=f"cq-{chat_id}-{int(time.time())}",
        description=f"{product['name']} - {product.get('days', 0)} days",
    )
    text = nowpayments.format_payment_instructions(payment)
    if "Invoice" in text:
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


def handle_coingate(chat_id, message_id, product_id=None):
    """Create a CoinGate order -> send the hosted web payment page link."""
    if not coingate.is_configured():
        kb = network_keyboard(product_id) if product_id else shop_keyboard()
        return edit_message(chat_id, message_id, lang.TXT["cg_coming_soon"], kb)

    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        return edit_message(chat_id, message_id, lang.TXT["product_sold_out"], shop_keyboard())

    order = coingate.create_order(
        price_usd=config.effective_price(product),
        title=product["name"],
        description=product.get("description", ""),
        order_id=f"cq-{chat_id}-{int(time.time())}",
    )
    if "error" in order or not order.get("payment_url"):
        return edit_message(chat_id, message_id, lang.TXT["np_error"], back_menu_keyboard())

    # Remember pending so auto-poll can deliver when paid.
    _save_pending(chat_id, {
        "gateway": "coingate",
        "payment_id": order.get("id"),
        "product_id": product.get("id"),
    })
    text = lang.TXT["cg_created"].format(
        price=order.get("price_amount"), currency=order.get("price_currency", "USD"),
        url_line=lang.TXT["cg_payment_url"].format(url=order.get("payment_url")),
    )
    return edit_message(chat_id, message_id, text, back_menu_keyboard())


def _finalize_coingate_paid(chat_id, order_id, product_id=None):
    """Deliver a confirmed CoinGate payment and clear pending (once)."""
    pending = _load_pending().get(str(chat_id))
    if not pending or pending.get("gateway") != "coingate":
        return None
    product = config.get_product(product_id) if product_id else config.get_default_product()
    if product is None:
        product = config.get_default_product() or {
            "id": None, "name": "item", "days": config.PREMIUM_DAYS, "kind": "channel"}
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    username = (sub or {}).get("username", "")
    msg, _ = _deliver_product(chat_id, username, product, "coingate")
    _save_pending(chat_id, "")
    return msg


def poll_pending_payments():
    """Background auto-poll of pending payments (NOWPayments + CoinGate).

    Like IPN but no server needed. Asks each gateway for status; when a
    payment is confirmed it delivers the product automatically and messages
    the customer.
    """
    pendings = _load_pending()
    if not pendings:
        return 0
    delivered = 0
    for chat_id, pending in list(pendings.items()):
        if not pending or pending == "":
            continue
        gateway = pending.get("gateway", "nowpayments")
        payment_id = pending.get("payment_id") if isinstance(pending, dict) else pending
        if not payment_id:
            continue
        if gateway == "coingate":
            order = coingate.get_order(payment_id)
            state = order.get("status") if isinstance(order, dict) else "invalid"
            if state == "paid":
                product_id = pending.get("product_id")
                msg = _finalize_coingate_paid(chat_id, payment_id, product_id)
                if msg:
                    send_message(chat_id, msg, back_menu_keyboard())
                    delivered += 1
                    print(f"   [auto] delivered CoinGate order {payment_id} for chat {chat_id}")
            continue
        # NOWPayments
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
    """Account page: membership date, ID, transaction count, total payments by coin."""
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)
    if not sub:
        text = lang.TXT["not_subscribed"]
    else:
        uid = chat_id
        since = sub.get("subscribed_at", "—")[:10]
        # Compute transaction stats from stored tx history.
        txns = sub.get("transactions", [])
        txn_count = len(txns)
        # Sum total payments by currency.
        by_coin = {}
        for t in txns:
            cur = (t.get("currency") or "USDT").upper()
            amt = float(t.get("amount") or 0)
            by_coin[cur] = by_coin.get(cur, 0) + amt
        payments_lines = "\n".join(f"- {cur}: {amt} {cur}" for cur, amt in by_coin.items()) if by_coin else "- No payments yet"
        text = lang.TXT["account_title"].format(since=since, uid=uid, txn_count=txn_count, payments=payments_lines)
    if message_id is not None:
        return edit_message(chat_id, message_id, text, back_menu_keyboard())
    return send_message(chat_id, text, back_menu_keyboard())


def handle_help(chat_id, message_id=None):
    text = lang.TXT["help"]
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
    elif cb_data == "owner_manage":
        # Owner-only management menu. Ignore if not the owner.
        if admin.is_owner(chat_id):
            edit_message(chat_id, message_id, lang.TXT["owner_menu_title"], owner_keyboard())
    elif cb_data == "owner_add_product":
        if admin.is_owner(chat_id):
            start_add_product_wizard(chat_id, message_id)
    elif cb_data == "wizard_cancel":
        if admin.is_owner(chat_id):
            _save_wizard_state(chat_id, None)
            edit_message(chat_id, message_id, lang.TXT["wizard_cancelled"], owner_keyboard())
    elif cb_data == "wizard_skip":
        if admin.is_owner(chat_id):
            # Skipping a step = an empty value for the current step.
            text, done = _advance_wizard(chat_id, "")
            if done:
                return
            edit_message(chat_id, message_id, text, wizard_keyboard())
    elif cb_data == "owner_list_products":
        if admin.is_owner(chat_id):
            _owner_list(chat_id, message_id)
    elif cb_data == "owner_howto_add":
        if admin.is_owner(chat_id):
            edit_message(chat_id, message_id, lang.TXT["owner_howto_text"], owner_keyboard())
    elif cb_data == "owner_remove_product":
        if admin.is_owner(chat_id):
            edit_message(chat_id, message_id, lang.TXT["owner_remove_title"], remove_product_keyboard())
    elif cb_data.startswith("rm_prod:"):
        if admin.is_owner(chat_id):
            pid = cb_data[len("rm_prod:"):]
            p = config.get_product(pid)
            if p:
                edit_message(chat_id, message_id,
                             lang.TXT["owner_confirm_remove"].format(name=p["name"]),
                             confirm_remove_keyboard(pid))
    elif cb_data.startswith("rm_confirm:"):
        if admin.is_owner(chat_id):
            pid = cb_data[len("rm_confirm:"):]
            p = config.get_product(pid)
            if p:
                config.PRODUCTS = [x for x in config.PRODUCTS if x.get("id") != pid]
                config.save_products()
                edit_message(chat_id, message_id,
                             lang.TXT["prod_removed"].format(name=p["name"]),
                             owner_keyboard())
    elif cb_data.startswith("cat_"):
        # Category selected in shop -> show products in that category.
        category = cb_data[len("cat_"):]
        edit_message(chat_id, message_id, lang.TXT["shop_title"], category_keyboard(category))
    elif cb_data == "wizard_back":
        if admin.is_owner(chat_id):
            text, ok = _wizard_back(chat_id)
            if ok:
                edit_message(chat_id, message_id, text, wizard_keyboard())
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
    elif cb_data == "pay_coingate" or cb_data.startswith("pay_coingate:"):
        product_id = None
        if ":" in cb_data:
            product_id = cb_data.split(":", 1)[1]
        handle_coingate(chat_id, message_id, product_id)
    elif cb_data == "check_payment":
        handle_check_payment(chat_id, username, message_id)
    elif cb_data == "pay_done":
        handle_pay_done(chat_id, message_id)
    elif cb_data == "status":
        handle_status(chat_id, message_id)
    elif cb_data == "website":
        if config.WEBSITE_URL:
            edit_message(chat_id, message_id, lang.TXT["website_open"].format(url=config.WEBSITE_URL))
        else:
            edit_message(chat_id, message_id, lang.TXT["website_missing"], back_menu_keyboard())
    elif cb_data == "support":
        if config.SUPPORT_URL:
            edit_message(chat_id, message_id, lang.TXT["support_open"].format(url=config.SUPPORT_URL))
        else:
            edit_message(chat_id, message_id, lang.TXT["support_missing"], back_menu_keyboard())
    elif cb_data == "account":
        handle_status(chat_id, message_id)
    elif cb_data == "help":
        handle_help(chat_id, message_id)


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
                price=config.effective_price(p), duration=lang.product_duration(p),
                kind=p.get("kind", "channel"),
            ))
        lines.append("")
        lines.append("Manage: /add_product, /remove_product <id>, /set_deliver <id> <text>")
        send_message(chat_id, "\n".join(lines), back_menu_keyboard())
        return True

    elif cmd.startswith("/add_product "):
        # Format: /add_product Name | price [| days [| kind]]
        # Only name and price are required. days defaults to PREMIUM_DAYS,
        # kind defaults to "channel". The owner only needs to give the
        # essentials (e.g. just name and price).
        spec = cmd[len("/add_product "):].strip()
        parts = [s.strip() for s in spec.split("|")]
        # require at least name and price
        if len(parts) < 2 or not parts[0] or not parts[1]:
            send_message(chat_id, lang.TXT["prod_usage_add"], back_menu_keyboard())
            return True
        try:
            name = parts[0]
            price = float(parts[1])
        except ValueError:
            send_message(chat_id, lang.TXT["prod_usage_add"], back_menu_keyboard())
            return True
        # optional: days (default) and kind (default channel)
        days = int(parts[2]) if len(parts) >= 3 and parts[2] else config.PREMIUM_DAYS
        kind = parts[3].lower() if len(parts) >= 4 and parts[3] else "channel"
        if kind not in ("channel", "digital"):
            kind = "channel"
        pid = name.lower().replace(" ", "_")[:20]
        new_id = pid
        n = 1
        while config.get_product(new_id):
            new_id = f"{pid}_{n}"; n += 1
        product = {
            "id": new_id, "name": name, "price_usd": price,
            "days": days, "kind": kind,
            "description": f"{name} — access to {name}.",
            "deliver": "" if kind == "digital" else None,
        }
        config.PRODUCTS.append(product)
        config.save_products()
        send_message(chat_id, lang.TXT["prod_added"].format(
            name=name, price=price, days=days, kind=kind, disc=""), back_menu_keyboard())
        if kind == "digital":
            send_message(chat_id, lang.TXT["prod_need_desc"], back_menu_keyboard())
        return True

    elif cmd.startswith("/remove_product "):
        pid = cmd[len("/remove_product "):].strip()
        product = config.get_product(pid)
        if product is None:
            send_message(chat_id, lang.TXT["prod_not_found"].format(id=pid), back_menu_keyboard())
            return True
        config.PRODUCTS = [p for p in config.PRODUCTS if p.get("id") != pid]
        config.save_products()
        send_message(chat_id, lang.TXT["prod_removed"].format(name=product["name"]), back_menu_keyboard())
        return True

    elif cmd.startswith("/set_deliver "):
        # Format: /set_deliver <id> <delivery text>
        rest = cmd[len("/set_deliver "):].strip()
        pid, _, deliver = rest.partition(" ")
        product = config.get_product(pid)
        if product is None:
            send_message(chat_id, lang.TXT["prod_not_found"].format(id=pid), back_menu_keyboard())
            return True
        product["deliver"] = deliver.strip()
        config.save_products()
        send_message(chat_id, lang.TXT["delivery_set"].format(name=product["name"]), back_menu_keyboard())
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
            send_message(chat_id, lang.TXT["err_format"].format(msg=err), back_menu_keyboard())
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
    elif command == "/status":
        handle_status(chat_id)
    elif command == "/help":
        handle_help(chat_id)
    elif not command.startswith("/"):
        # Free text. Priority 1: the owner is mid add-product wizard.
        if admin.is_owner(chat_id) and _load_wizard().get(str(chat_id), {}).get("active"):
            text, done = _advance_wizard(chat_id, command)
            if done:
                return
            if text:
                send_message(chat_id, text, wizard_keyboard())
            return
        # Priority 2: user is mid-payment (selected network + tapped "I paid"),
        # so free text is a transaction hash.
        pending = _load_pending().get(str(chat_id))
        if isinstance(pending, dict) and pending.get("product_id") and command.strip():
            handle_pay(chat_id, username, command.strip())
            return
        send_message(chat_id, lang.TXT["unknown_command"], main_menu_keyboard(chat_id))
    else:
        send_message(chat_id, lang.TXT["unknown_command"], main_menu_keyboard(chat_id))


# ---------------------------------------------------------------------------
# Main polling loop

def _payment_poller_loop():
    """Run payment polling in a background thread so it never blocks message
    handling (a slow NOWPayments call would otherwise freeze the bot)."""
    while True:
        try:
            if nowpayments.is_configured():
                poll_pending_payments()
        except Exception as e:
            print("payment-poll error:", e)
        time.sleep(8)  # poll every 8s in the background

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
    if nowpayments.is_configured():
        t = threading.Thread(target=_payment_poller_loop, daemon=True)
        t.start()
        print("   Payment poller running in background thread")

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

        time.sleep(0.3)

if __name__ == "__main__":
    main()
