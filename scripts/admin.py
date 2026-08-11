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

All settings come from ``config`` (single source of truth). This module has NO
duplicated .env loading.
"""
import json
import os
import datetime

import config


def is_owner(chat_id):
    """True if the given chat_id is the configured owner."""
    return bool(config.OWNER_CHAT_ID) and str(chat_id) == str(config.OWNER_CHAT_ID)


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


def add_premium_member(path, user_id, days=None):
    """Add/upgrade a user to premium for N days. Returns an error string or None."""
    if days is None:
        days = config.PREMIUM_DAYS
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
    print("OWNER_CHAT_ID:", config.OWNER_CHAT_ID or "(not set)")
    print("is_owner test with none:", is_owner(None))
