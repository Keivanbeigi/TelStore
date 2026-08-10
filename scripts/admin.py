#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin panel for the Crypto Quest bot owner
==========================================
Owner-only commands to manage subscribers, broadcast, and set prices.

Owner is identified by OWNER_CHAT_ID in .env (their Telegram chat_id).
Get it from @userinfobot.

Owner commands:
  /stats                - subscriber + revenue summary
  /broadcast <text>     - send a message to all subscribers
  /add_member <user_id> - manually grant premium (30 days)
  /kick <user_id>       - remove a subscriber (and revoke channel access)
  /set_price <usd>      - change the monthly premium price
  /admin                - list owner commands
"""
import json
import os
import re
import datetime


def _env_file():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def _load_env_str(key, default=""):
    val = os.environ.get(key, "").strip()
    if val:
        return val
    if os.path.exists(_env_file()):
        try:
            with open(_env_file(), "r", encoding="utf-8-sig") as f:
                m = re.search(rf'^{key}=([^\r\n]+)', f.read(), re.M)
            if m:
                return m.group(1).strip().strip('"').strip("'")
        except Exception:
            pass
    return default

OWNER_CHAT_ID = _load_env_str("OWNER_CHAT_ID", "").strip()

def is_owner(chat_id):
    """True if the given chat_id is the configured owner."""
    return bool(OWNER_CHAT_ID) and str(chat_id) == str(OWNER_CHAT_ID)

def load_subscribers(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"subscribers": []}

def save_subscribers(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def stats_text(subscribers_file):
    """Build a stats summary from subscribers.json."""
    data = load_subscribers(subscribers_file)
    subs = data.get("subscribers", [])
    total = len(subs)
    premium = [s for s in subs if s.get("plan") == "premium"]
    free = [s for s in subs if s.get("plan") == "free"]
    # Estimate revenue from premium count * price (price from subscribers is not stored, use premium count only)
    active_premium = sum(
        1 for s in premium if s.get("premium_until")
    )
    lines = [
        "📊 Subscriber statistics:",
        "",
        f"👥 Total subscribers: {total}",
        f"💎 Premium: {len(premium)}",
        f"🆓 Free: {len(free)}",
        "",
        "💰 Estimated monthly revenue:",
    ]
    # Price is read from the caller (PRICE_CRYPTO_USD). Passed via message or recomputed.
    return lines

def add_premium_member(path, user_id, days=30):
    """Add/upgrade a user to premium for N days. Returns an error string or None."""
    data = load_subscribers(path)
    subs = data.get("subscribers", [])
    now = datetime.datetime.now()
    found = None
    for s in subs:
        if str(s.get("chat_id")) == str(user_id):
            found = s
            break
    until = (now + datetime.timedelta(days=days)).isoformat()
    if found:
        found["plan"] = "premium"
        found["premium_until"] = until
        found["payment_method"] = "manual"
    else:
        subs.append({
            "chat_id": str(user_id),
            "username": "",
            "plan": "premium",
            "subscribed_at": now.isoformat(),
            "premium_until": until,
            "payment_method": "manual",
        })
        data["subscribers"] = subs
    save_subscribers(path, data)
    return None

def remove_member(path, user_id):
    """Remove a user from subscribers. Returns True if removed."""
    data = load_subscribers(path)
    before = len(data.get("subscribers", []))
    data["subscribers"] = [s for s in data.get("subscribers", []) if str(s.get("chat_id")) != str(user_id)]
    changed = len(data["subscribers"]) != before
    if changed:
        save_subscribers(path, data)
    return changed


if __name__ == "__main__":
    print("OWNER_CHAT_ID:", OWNER_CHAT_ID or "(not set)")
    print("is_owner test with none:", is_owner(None))