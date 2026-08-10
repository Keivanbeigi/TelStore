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

Configuration (.env):
  CHANNEL_ID   = Telegram channel id, e.g. -1001234567890
  CHANNEL_LINK = public invite link, e.g. https://t.me/yourchannel  (optional)
  (If CHANNEL_ID is empty, the bot skips membership and only sells access.)
"""
import json
import os
import re
import datetime
import urllib.request
import urllib.parse

# Bot token is needed to call the API. Reuse the same loading logic as bot.py.
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

TOKEN = _load_env_str("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = _load_env_str("CHANNEL_ID", "")        # e.g. -1001234567890
CHANNEL_LINK = _load_env_str("CHANNEL_LINK", "")    # optional public invite link

def is_configured():
    """True if a channel id is configured (membership management is active)."""
    return bool(CHANNEL_ID)

def _api_call(method, **params):
    """Call a Telegram Bot API method. Returns parsed JSON or None."""
    if not TOKEN:
        return None
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
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
    inv = _api_call("createChatInviteLink", chat_id=CHANNEL_ID,
                    member_limit=1, expire_date=0)
    if inv and inv.get("ok"):
        link = inv.get("result", {}).get("invite_link")

    # 2) If a public channel link is configured, fall back to it.
    if not link:
        link = CHANNEL_LINK

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
    # Ban removes the member; unban is needed so they could rejoin later.
    banned = _api_call("banChatMember", chat_id=CHANNEL_ID, user_id=user_id)
    _api_call("unbanChatMember", chat_id=CHANNEL_ID, user_id=user_id)
    return bool(banned and banned.get("ok"))

def is_member(user_id):
    """Check if a user is currently a member of the channel."""
    if not is_configured():
        return None  # unknown - not managing membership
    res = _api_call("getChatMember", chat_id=CHANNEL_ID, user_id=user_id)
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
            # Compare naive datetimes (drop tz for simplicity)
            until_naive = until.replace(tzinfo=None)
        except Exception:
            continue
        if until_naive < now:
            # Premium expired -> kick from channel and downgrade to free.
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
        print("CHANNEL_ID:", CHANNEL_ID)
        print("CHANNEL_LINK:", CHANNEL_LINK or "(none)")
    else:
        print("Put CHANNEL_ID in .env to enable membership management.")