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
        "Access our private VIP channel, buy digital products and more — "
        "pay with crypto, delivered instantly.\n"
        "Choose an option below to get started 👇"
    ),

    # --- subscribe ---
    "already_subscribed": "✅ You are already subscribed! Check your status below 👇",
    "free_activated": (
        "🆓 Free subscription activated!\n"
        "You'll get updates from the shop.\n\n"
        "💎 Check the shop for VIP access and products."
    ),

    # --- products / shop ---
    "shop_title": "🛒 Shop — choose a product to buy:",
    "product_page": (
        "{emoji} {name}\n\n"
        "{description}\n\n"
        "💰 Price: ${price:.2f}\n"
        "⏳ Access: {duration}\n\n"
        "Select a payment network:"
    ),
    "duration_days": "{days} days",
    "duration_lifetime": "Lifetime",
    "product_sold_out": "⚠️ This product is not available right now.",

    # --- delivery (after payment) ---
    "pay_received_channel": (
        "✅ Crypto payment received! (tx: {tx})\n"
        "Your access is active for {days} days."
    ),
    "pay_received_digital": (
        "✅ Crypto payment received! (tx: {tx})\n"
        "Here's what you bought:\n\n{deliver}"
    ),

    # --- premium / payment ---
    "premium_active_until": "💎 Your access is active until {until}",
    "premium_offer": (
        "💎 Payment — {name}\n"
        "💰 Price: ${price:.2f}\n\n"
        "Select your payment network:"
    ),
    "pay_howto": "✅ Great! Send the amount to the wallet address above.\n\n"
                 "After the transaction, send the **tx hash** here to confirm.",
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
    "np_no_pending": "No pending payment found. Tap a product to start a new one.",
    "np_payment_confirmed": "✅ Payment confirmed! 🎉\nYour access is now active for {days} days.",
    "np_waiting": "⏳ Payment status: **{state}**\n\n"
                  "Send the exact amount to the address above, then check again in a minute.",
    "np_error": "⚠️ Could not check payment status. Please try again in a moment.",

    # --- CoinGate (web payment page) ---
    "cg_coming_soon": (
        "💳 Online crypto checkout coming soon!\n\n"
        "For now, use NOWPayments or the manual wallet address below."
    ),
    "cg_no_pending": "No pending CoinGate payment found. Choose a product to start a new one.",
    "cg_payment_url": "🔗 Open this payment page in your browser:\n{url}",
    "cg_created": (
        "💳 Pay online with crypto (CoinGate)\n\n"
        "💰 Amount: {price} {currency}\n"
        "{url_line}\n\n"
        "Pay with BTC, ETH, USDT and 70+ coins. Once confirmed, the product "
        "is delivered automatically."
    ),

    # --- status ---
    "not_subscribed": "You are not subscribed. Tap \"Free Subscription\" to start.",
    "status": "📊 Subscription status:\n\n"
             "Plan: {plan}\n"
             "Member since: {since}\n"
             "Premium until: {until}",

    # --- help ---
    "help": (
        "❓ Help:\n\n"
        "🛒 Shop - browse and buy products (VIP access, digital items)\n"
        "🆓 Free subscription - shop updates\n"
        "📊 Status - your access info\n"
        "🚫 Unsubscribe - cancel membership\n\n"
        "To pay with crypto, pick a product, then a network, and send the amount "
        "to the wallet address."
    ),

    # --- unsubscribe ---
    "unsubscribed": "🚫 Your subscription has been cancelled.",
    "not_subscribed_2": "You are not subscribed.",

    # --- unknown / generic ---
    "unknown_command": "❓ Unknown command. Choose from the menu.",
    "coming_soon": "🚧 Coming soon.",

    # --- payment format (crypto) ---
    "pay_price": "💰 Price: ${price:.2f}",
    "pay_network": "🌐 Network: {name} ({standard})",
    "pay_network_recommended": "🌐 Network: ⭐ Recommended - {name} ({standard})",
    "pay_token": "   Token: {currency}",
    "pay_wallet_label": "🏦 Wallet address (all networks):",
    "pay_wallet_missing": (
        "⚠️ The owner has not set a wallet yet. Payment is paused.\n"
        "Contact the owner to configure CRYPTO_ADDRESS in `.env`."
    ),
    "pay_amount": "📤 Send exactly ${price:.2f} worth (plus network fee).",
    "pay_after": "✅ After paying, tap \"I paid\" and send the transaction hash.",

    # --- status plan labels ---
    "plan_premium": "💎 Premium",
    "plan_free": "🆓 Free",

    # --- owner admin panel ---
    "admin_stats": ("📊 Subscriber statistics:\n\n"
                    "👥 Total: {total}\n"
                    "💎 Premium/Paid: {premium}\n"
                    "🆓 Free: {free}\n\n"
                    "💰 Est. revenue: ${revenue:.2f}"),
    "admin_help": ("🛠 Owner commands:\n\n"
                   "📊 /stats - member & revenue summary\n"
                   "📢 /broadcast <text> - message all subscribers\n"
                   "➕ /add_member <user_id> - grant paid access ({days} days)\n"
                   "🚫 /kick <user_id> - remove a member\n"
                   "🛒 /products - list products\n"
                   "➕ /add_product Name|price|days|kind - add a product\n"
                   "➖ /remove_product <id> - remove a product\n"
                   "📦 /set_deliver <id> <text> - set digital delivery text\n"
                   "💰 /set_price <usd> - change the default price (current run)"),
    "broadcast_sent": "📢 Broadcast sent to {sent} subscriber(s).",
    "broadcast_partial": " ({failed} failed)",
    "broadcast_msg": "📢 {msg}",
    "invalid_user_id": "❌ Invalid user id.",
    "member_granted": "✅ Premium granted to {uid} for {days} days.",
    "member_granted_channel": "\n🔓 Channel invite:\n{link}",
    "member_removed": "🚫 Removed {uid}.",
    "member_not_found": "⚠️ {uid} was not a subscriber.",
    "invalid_price": "❌ Invalid price. Use /set_price 5.0",
    "price_updated": "💰 Price updated to ${price:.2f} (current run).",
    "admin_denied": "⛔ You don't have permission to use owner commands.",
    "products_title": "🛒 Configured products (edit config.py → PRODUCTS):",
    "products_line": "  • {emoji} {name} — ${price:.2f} ({duration}, kind={kind})",
    "emoji_default": "🛍️",
    "prod_added": "✅ Product added: {name} (${price:.2f}, {days} days, {kind})",
    "prod_removed": "🚫 Product removed: {name}",
    "prod_not_found": "⚠️ No product with id: {id}",
    "prod_usage_add": ("❌ Usage: /add_product <name> | <price> | <days> | <kind>\n"
                       "  kind = channel (VIP access) or digital (send a link).\n"
                       "  days = 0 for lifetime. Example:\n"
                       "  /add_product VIP Year | 49.99 | 365 | channel"),
    "prod_usage_remove": "❌ Usage: /remove_product <id>",
    "prod_need_desc": "For a digital product, set its delivery text with /set_deliver <id> <text>.",
    "owner_menu_title": "⚙️ Owner Menu — manage your products & shop.",
    "owner_howto_text": (
        "How to add a product (type this to the bot):\n\n"
        "/add_product Name | price | days | kind\n\n"
        "Examples:\n"
        "  /add_product VIP Month | 5.00 | 30 | channel\n"
        "  /add_product Crypto Course | 19.99 | 0 | digital\n\n"
        "  kind = channel (VIP access) or digital (send link/text)\n"
        "  days = 0 for lifetime\n\n"
        "After adding a digital product, set what the buyer gets:\n"
        "  /set_deliver <id> <text>\n\n"
        "Remove a product:\n"
        "  /remove_product <id>"
    ),
    "owner_edit_menu": "⚙️ Edit Menu",
    "owner_edit_menu_title": "⚙️ Edit the main menu. Tap a button to toggle it:",
    "owner_remove_title": "🗑️ Tap a product to remove it:",
    "owner_confirm_remove": "⚠️ Remove \"{name}\"?",
    "owner_menu_updated": "✅ Menu updated.",
    "owner_menu_hidden_note": "(hidden buttons show dimmed below)",
    "sale_notification": "🛎️ NEW SALE!\n\n🛒 Product: {name}\n💰 Price: ${price:.2f}\n👤 Buyer: {user}\n💳 Method: {method}\n🕐 {time}",
}


# ---------------------------------------------------------------------------
#  Button / keyboard labels
# ---------------------------------------------------------------------------
BTN = {
    "shop": "🛒 Shop / Products",
    "free_sub": "🆓 Free Subscription",
    "status": "📊 My Status",
    "help": "❓ Help",
    "unsubscribe": "🚫 Unsubscribe",
    "back_menu": "◀️ Back to menu",
    "back_shop": "◀️ Back to shop",
    "pay_nowpayments": "💳 Pay with Card / Crypto (NOWPayments)",
    "pay_coingate": "🌐 Pay online (web page)",
    "pay_done": "✅ I paid",
    "check_payment": "🔎 Check payment status",
    "recommended_bsc": "⭐ {name} (Recommended)",
    "owner_manage": "⚙️ Owner Menu",
    "owner_add_product": "➕ Add Product",
    "owner_list_products": "🛒 List Products",
    "owner_howto_add": "❓ How to add",
    "owner_edit_menu": "⚙️ Edit Menu",
    "owner_remove_product": "🗑️ Remove Product",
    "owner_confirm_yes": "✅ Yes, remove",
    "owner_confirm_no": "❌ Cancel",
    "back": "◀️ Back",
}


# ---------------------------------------------------------------------------
#  Product helpers (button labels & callbacks, driven by config.PRODUCTS)
# ---------------------------------------------------------------------------
def product_button(p):
    """Short button label for a product dict from config.PRODUCTS."""
    return f"{p.get('emoji', TXT['emoji_default'])} {p['name']} — ${p['price_usd']:.2f}"


def product_callback(p):
    """Callback data to select a product (\"prod_<id>\")."""
    return f"prod_{p['id']}"


def product_duration(p):
    """Human text for how long access lasts. 0 = lifetime."""
    days = p.get("days", 0)
    if days:
        return TXT["duration_days"].format(days=days)
    return TXT["duration_lifetime"]


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
