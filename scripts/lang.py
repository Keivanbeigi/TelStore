#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
All user-facing strings for the Crypto Quest bot
==================================================
Every static message, button label, and callback label lives here in one
place. This lets you translate or reword the whole bot without touching the
handler logic in bot.py.

Everything is in English (product is sold internationally).

Usage inside bot.py:
    from lang import TXT, key...
    send_message(chat_id, TXT["welcome"], KEY_MAIN_MENU)
"""
# ---------------------------------------------------------------------------
#  Text messages (the @-free, {placeholder} style uses str.format later)
# ---------------------------------------------------------------------------
TXT = {
    # --- main menu / welcome ---
    "welcome": (
        "👋 Welcome to Crypto Quest!\n\n"
        "Get daily reports on XP farming missions and badges.\n"
        "Choose an option below to get started 👇"
    ),

    # --- subscribe ---
    "already_subscribed": "✅ You are already subscribed! Check your status below 👇",
    "free_activated": (
        "🆓 Free subscription activated!\n"
        "You'll receive a weekly missions report.\n\n"
        "💎 For the daily report (every 6 hours), tap \"Buy Premium\"."
    ),

    # --- premium / payment ---
    "premium_active_until": "💎 You are Premium until {until}",
    "premium_offer": (
        "💎 Premium subscription - daily report every 6 hours\n"
        "💰 Price: ${price}/month\n\n"
        "Select your payment network:"
    ),
    "pay_howto": "✅ Great! Send the amount to the wallet address above.\n\n"
                 "After the transaction, send the **tx hash** here to confirm.",
    "pay_received": (
        "✅ Crypto payment received! (tx: {tx})\n"
        "Your Premium is active for {days} days."
    ),
    "pay_awaiting_confirm": "\n\n(Awaiting final confirmation.)",

    # --- channel access ---
    "channel_granted": "\n\n🔓 VIP channel access granted! Join here:\n{link}",
    "channel_note": "\n\n{note}",

    # --- NOWPayments ---
    "np_coming_soon": (
        "💳 Card / crypto payments coming soon!\n\n"
        "For now, use the manual wallet address from the network options "
        "below to pay directly."
    ),
    "np_no_pending": "No pending payment found. Tap \"Buy Premium\" to start a new one.",
    "np_payment_confirmed": "✅ Payment confirmed! 🎉\nYour Premium is now active for {days} days.",
    "np_waiting": "⏳ Payment status: **{state}**\n\n"
                  "Send the exact amount to the address above, then check again in a minute.",
    "np_error": "⚠️ Could not check payment status. Please try again in a moment.",

    # --- status ---
    "not_subscribed": "You are not subscribed. Tap \"Free Subscription\" to start.",
    "status": "📊 Subscription status:\n\n"
             "Plan: {plan}\n"
             "Member since: {since}\n"
             "Premium until: {until}",

    # --- help ---
    "help": (
        "❓ Help:\n\n"
        "💎 Buy Premium - daily report every 6 hours (${price}/month)\n"
        "🆓 Free subscription - weekly report\n"
        "📊 Status - your subscription info\n"
        "🚫 Unsubscribe - cancel membership\n\n"
        "To pay with crypto, pick a network and send the amount to the wallet address."
    ),

    # --- unsubscribe ---
    "unsubscribed": "🚫 Your subscription has been cancelled.",
    "not_subscribed_2": "You are not subscribed.",

    # --- unknown / generic ---
    "unknown_command": "❓ Unknown command. Choose from the menu.",
    "coming_soon": "🚧 Coming soon.",

    # --- payment format (crypto) ---
    "pay_price": "💰 Price: ${price}/month",
    "pay_network": "🌐 Network: {name} ({standard})",
    "pay_network_recommended": "🌐 Network: ⭐ Recommended - {name} ({standard})",
    "pay_token": "   Token: {currency}",
    "pay_wallet_label": "🏦 Wallet address (all networks):",
    "pay_amount": "📤 Send exactly ${price} worth (plus network fee).",
    "pay_after": "✅ After paying, tap \"I paid\" and send the transaction hash.",

    # --- status plan labels ---
    "plan_premium": "💎 Premium",
    "plan_free": "🆓 Free",

    # --- owner admin panel ---
    "admin_stats": ("📊 Subscriber statistics:\n\n"
                    "👥 Total: {total}\n"
                    "💎 Premium: {premium}\n"
                    "🆓 Free: {free}\n\n"
                    "💰 Est. monthly revenue: ${revenue:.2f}"),
    "admin_help": ("🛠 Owner commands:\n\n"
                   "📊 /stats - subscriber & revenue summary\n"
                   "📢 /broadcast <text> - message all subscribers\n"
                   "➕ /add_member <user_id> - grant premium ({days} days)\n"
                   "🚫 /kick <user_id> - remove a subscriber\n"
                   "💰 /set_price <usd> - change monthly price"),
    "broadcast_sent": "📢 Broadcast sent to {sent} subscriber(s).",
    "broadcast_partial": " ({failed} failed)",
    "broadcast_msg": "📢 {msg}",
    "invalid_user_id": "❌ Invalid user id.",
    "member_granted": "✅ Premium granted to {uid} for {days} days.",
    "member_granted_channel": "\n🔓 Channel invite:\n{link}",
    "member_removed": "🚫 Removed {uid}.",
    "member_not_found": "⚠️ {uid} was not a subscriber.",
    "invalid_price": "❌ Invalid price. Use /set_price 5.0",
    "price_updated": "💰 Price updated to ${price:.2f}/month (for this run).",
    "admin_denied": "⛔ You don't have permission to use owner commands.",
}


# ---------------------------------------------------------------------------
#  Button / keyboard labels
# ---------------------------------------------------------------------------
BTN = {
    "buy_premium": "💎 Buy Premium - ${price}/month",
    "free_sub": "🆓 Free Subscription",
    "status": "📊 Subscription Status",
    "help": "❓ Help",
    "unsubscribe": "🚫 Unsubscribe",
    "back_menu": "◀️ Back to menu",
    "pay_nowpayments": "💳 Pay with Card / Crypto (NOWPayments)",
    "pay_done": "✅ I paid",
    "check_payment": "🔎 Check payment status",
    "recommended_bsc": "⭐ {name} (Recommended)",
}


# ---------------------------------------------------------------------------
#  Payment network order / labels (drive keyboard)
# ---------------------------------------------------------------------------
def network_button(net):
    """Pretty button label for a payment network dict from config.CRYPTO_NETWORKS.

    Reads the network's own fields (``name``, ``standard``, ``recommended``) so
    that adding a new network to ``config.CRYPTO_NETWORKS`` needs no change here.
    Recommended networks keep a short label ("⭐ BSC (Recommended)"); the others
    show their standard ("Ethereum (ERC-20)").
    """
    if net.get("recommended"):
        return BTN["recommended_bsc"].format(name=net["name"])
    label = net["name"]
    if net.get("standard"):
        label += f" ({net['standard']})"
    return label


def network_callback(net):
    """Callback data for a network (\"pay_bsc\", \"pay_ethereum\", \"pay_polygon\")."""
    return f"pay_{net['name'].lower()}"
