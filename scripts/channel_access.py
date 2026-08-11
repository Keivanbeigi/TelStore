#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Channel membership management for the Crypto Quest bot
=======================================================
Manages automatic VIP channel membership for paid subscribers.

How it works
------------
The bot owner makes the bot an ADMIN of their VIP Telegram channel
(Management -> Administrators -> add bot, with "ban users" permission).
Then when a customer completes payment:
  - grant_access(): create a private invite link and send it to the customer
  - revoke_access(): ban the member (kicks them out) when their plan expires
  - check_expired(): periodic sweep that kicks expired premium members

All settings (TOKEN, CHANNEL_ID, CHANNEL_LINK) come from ``config`` so there
is a single source of truth.
"""
import json
import os
import datetime
import urllib.request
import urllib.parse

import config


def is_configured():
    """True if a channel id is configured (membership management is active)."""
    return bool(config.CHANNEL_ID)


def _api_call(method, **params):
    """Call a Telegram Bot API method. Returns parsed JSON or None."""
    if not config.TOKEN:
        return None
    url = f"https://api.telegram.org/bot{config.TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"channel api error [{method}]:", e)
        return None


def grant_access(chat_id):
    """
    Grant a customer access to the VIP channel.
    Returns a dict with a message for the user, or an error dict.
    """
    if not is_configured():
        # No channel configured - just confirm subscription without membership.
        return {"ok": True, "channel": False}

    # 1) Try to create a private invite link (bot must be admin).
    link = None
    inv = _api_call("createChatInviteLink", chat_id=config.CHANNEL_ID,
                    member_limit=1, expire_date=0)
    if inv and inv.get("ok"):
        link = inv.get("result", {}).get("invite_link")

    # 2) If a public channel link is configured, fall back to it.
    if not link:
        link = config.CHANNEL_LINK

    if not link:
        return {"ok": True, "channel": False,
                "message": "Access granted. (Channel invite unavailable - contact support for the channel link.)"}

    return {"ok": True, "channel": True, "invite_link": link}


def revoke_access(user_id):
    """
    Kick a user out of the VIP channel (ban then unban, which removes them).
    Returns True on success.
    """
    if not is_configured():
        return False
    banned = _api_call("banChatMember", chat_id=config.CHANNEL_ID, user_id=user_id)
    _api_call("unbanChatMember", chat_id=config.CHANNEL_ID, user_id=user_id)
    return bool(banned and banned.get("ok"))


def is_member(user_id):
    """Check if a user is currently a member of the channel."""
    if not is_configured():
        return None  # unknown - not managing membership
    res = _api_call("getChatMember", chat_id=config.CHANNEL_ID, user_id=user_id)
    if res and res.get("ok"):
        status = res.get("result", {}).get("status", "")
        return status in ("member", "administrator", "creator")
    return None


def check_expired(subscribers_file):
    """
    Periodic sweep: remove expired premium members from the channel.
    `subscribers_file` is the path to subscribers.json.
    Returns a list of kicked user ids (chat ids).
    """
    kicked = []
    if not is_configured():
        return kicked
    try:
        with open(subscribers_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return kicked

    now = datetime.datetime.now()
    changed = False
    for sub in data.get("subscribers", []):
        if sub.get("plan") != "premium":
            continue
        until_raw = sub.get("premium_until")
        if not until_raw:
            continue
        try:
            until = datetime.datetime.fromisoformat(str(until_raw).replace("Z", "+00:00"))
            until_naive = until.replace(tzinfo=None)
        except Exception:
            continue
        if until_naive < now:
            user_id = str(sub.get("chat_id"))
            if revoke_access(user_id):
                kicked.append(user_id)
            sub["plan"] = "free"
            sub["premium_until"] = None
            changed = True

    if changed:
        try:
            with open(subscribers_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return kicked


if __name__ == "__main__":
    print("channel configured:", is_configured())
    if is_configured():
        print("CHANNEL_ID:", config.CHANNEL_ID)
        print("CHANNEL_LINK:", config.CHANNEL_LINK or "(none)")
    else:
        print("Put CHANNEL_ID in .env to enable membership management.")
