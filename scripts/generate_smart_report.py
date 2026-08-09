#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تولید گزارش هوشمند فارمینگ XP با هوش مصنوعی (OpenRouter)
=============================================================
این اسکریپت از OpenRouter (بدون نیاز به Google API) استفاده می‌کند تا
یک گزارش واقعی و به‌روز از ماموریت‌های فارمینگ XP بنویسد.

نیازمندی‌ها:
- OPENROUTER_API_KEY از محیط (یا فایل)
- دسترسی به اینترنت

خروجی: report.txt (گزارش آماده ارسال به تلگرام)
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
import datetime

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# مدل رایگان و قدرتمند برای تولید گزارش
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


def load_openrouter_key():
    """Load OpenRouter API key from env or known files."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    # Try known files
    candidates = [
        os.path.expanduser("~/.openrouter.env"),
        r"C:\Users\keiva\OneDrive\Desktop\New folder\Openrouter API for 9router.txt",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                m = re.search(r"(sk-or-[A-Za-z0-9_-]+)", content)
                if m:
                    return m.group(1).strip()
            except Exception:
                pass
    raise SystemExit("ERROR: OpenRouter API key not found")


def build_prompt():
    """Build a prompt asking the AI for a current crypto farming report."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""You are a crypto farming expert. Today is {now}. Write a SHORT, practical daily report in Persian (Farsi) about earning crypto via XP/badges on Galxe, Layer3, and Zealy.

The report must be:
- In Persian, concise (under 300 words)
- Structured with these sections (use simple emoji + plain text, NO markdown bold like ** or headers like ##)
- 3-5 recommended low-risk quests (social follows, communities, testnet swap/bridge/mint)
- A reminder that all tasks must be done manually (bots/automation are banned and cause bans)
- Direct links: Galxe https://galxe.com/quests, Layer3 https://layer3.xyz/quests, Zealy https://zealy.io/
- End with: use the dashboard to track progress

Output ONLY the report text, nothing else."""


def call_openrouter(prompt, api_key, model=DEFAULT_MODEL):
    """Call OpenRouter chat completions API."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You write practical, concise crypto guides."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 600,
        "temperature": 0.7,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return f"[ERROR] OpenRouter HTTP {e.code}: {body[:200]}"
    except Exception as e:
        return f"[ERROR] {e}"


def main():
    try:
        api_key = load_openrouter_key()
    except SystemExit as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    prompt = build_prompt()
    report = call_openrouter(prompt, api_key)

    if report.startswith("[ERROR]"):
        print(report, file=sys.stderr)
        sys.exit(1)

    # Sanitize: replace problematic characters for Telegram (e.g. heavy box lines)
    report = report.replace("\u2500", "-")  # ─ → -

    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(f"✅ گزارش هوشمند ساخته شد: {len(report)} کاراکتر")


if __name__ == "__main__":
    main()