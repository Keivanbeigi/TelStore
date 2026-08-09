#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تولید گزارش روزانه فارمینگ XP — برای GitHub Actions
این اسکریپت یک گزارش ساده می‌سازد و در report.txt ذخیره می‌کند.
"""
import datetime

def build_report():
    now = datetime.datetime.now()
    return f"""📊 گزارش فارمینگ XP
━━━━━━━━━━━━━━━━
📅 {now.strftime('%Y-%m-%d %H:%M')}

✅ این گزارش به صورت خودکار از GitHub Actions ارسال می‌شود.

💡 پیشنهادهای امروز برای کسب XP:
1. Galxe - ماموریت‌های روزانه و بج‌های رایگان
   https://galxe.com/quests
2. Layer3 - کوئست‌های XP
   https://layer3.xyz/quests
3. Zealy - ماموریت‌های اجتماعی
   https://zealy.io/

⚠️ همه کارها را دستی انجام دهید. ربات و اتوماسیون ممنوع است.
📈 پیشرفت خود را با داشبورد ثبت کنید.
"""

if __name__ == "__main__":
    report = build_report()
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("گزارش ساخته شد:", len(report), "کاراکتر")