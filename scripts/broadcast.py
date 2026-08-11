#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broadcast a report to all channel subscribers
===============================================
Sends a report to subscribers:
- Premium subscribers -> daily report (every 6 hours)
- Free subscribers -> only on Sundays (optional)

Configured via scripts/config.py (reads the project `.env`).

Usage:
  python broadcast.py --file report.txt            # send to all premium + free
  python broadcast.py --file report.txt --premium  # send to premium only
  python broadcast.py --file report.txt --test     # send to yourself only (test)
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request
import urllib.parse

import config


def load_subscribers():
    if os.path.exists(config.SUBSCRIBERS_FILE):
        with open(config.SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("subscribers", [])
    return []


def send_one(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("ok", False)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--premium", action="store_true", help="send to premium only")
    ap.add_argument("--test", action="store_true", help="send only to the test chat id")
    args = ap.parse_args()

    if not config.TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        print("ERROR: empty report", file=sys.stderr)
        sys.exit(1)

    token = config.TOKEN

    if args.test:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", config.OWNER_CHAT_ID)
        if not chat_id:
            print("ERROR: --test needs TELEGRAM_CHAT_ID or OWNER_CHAT_ID", file=sys.stderr)
            sys.exit(1)
        ok = send_one(token, chat_id, text)
        print(f"✅ test sent to {chat_id}" if ok else "❌ test failed")
        sys.exit(0 if ok else 1)

    subs = load_subscribers()
    if not subs:
        print("❌ no subscribers found")
        sys.exit(1)

    today = datetime.date.today().isoweekday()  # 1=Mon ... 7=Sun
    sent = 0
    for s in subs:
        plan = s.get("plan", "free")
        chat_id = s.get("chat_id")
        if not chat_id:
            continue
        if args.premium and plan != "premium":
            continue
        # free: only on Sundays (7)
        if not args.premium and plan == "free" and today != 7:
            continue
        if send_one(token, chat_id, text):
            sent += 1

    print(f"✅ Sent to {sent} subscriber(s)")
    sys.exit(0 if sent > 0 else 1)


if __name__ == "__main__":
    main()
