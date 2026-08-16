#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
All user-facing strings for the TelStore bot
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
    # --- brand / identity ---
    # Display name of the bot. Change this to rebrand the whole store without
    # touching any handler logic.
    "bot_name": "TelStore",

    # --- main menu / welcome ---
    "welcome": (
        "👋 Welcome to {name}!\n\n"
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
            "{model_line}"
            "{description}\n\n"
            "{price_line}"
            "⏳ Access: {duration}\n\n"
            "Select a payment network:"
        ),
        "model_line": "🏷️ Model: {model}\n",
        "model_line_empty": "",
        "price_normal": "💰 Price: ${price:.2f}\n",
    "price_discounted": "💰 Price: ${orig:.2f} ({discount:.0f}% off) = ${price:.2f}\n",
    "duration_days": "{days} days",
    "duration_lifetime": "Lifetime",
    "product_sold_out": "⚠️ This product is not available right now.",

    # --- shop category headers (products are grouped by kind) ---
    "cat_channel": "📺 Channel Access",
    "cat_digital": "📦 Digital Products",
    "cat_other": "🛍️ Products",

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
        "📊 Status - your access info\n\n"
        "To pay with crypto, pick a product, then a network, and send the amount "
        "to the wallet address."
    ),

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
    "admin_stats": ("📊 Store stats:\n"
                    "👥 Total members: {total}\n"
                    "💎 Premium: {premium}\n"
                    "🆓 Free: {free}\n\n"
                    "💰 Est. revenue: ${revenue:.2f}"),
    "settings_title": ("⚙️ Store settings (current values):\n\n"
                       "🏦 CHANNEL_ID: {channel_id}\n"
                       "🔗 CHANNEL_LINK: {channel_link}\n"
                       "🌐 WEBSITE_URL: {website}\n"
                       "💬 SUPPORT_URL: {support}\n\n"
                       "Change with:\n"
                       "🔧 /set_setting CHANNEL_LINK https://t.me/yourchannel\n"
                       "🔧 /set_setting WEBSITE_URL https://your-site.com\n"
                       "🔧 /set_setting SUPPORT_URL https://t.me/you\n\n"
                       "Send an empty value to clear a setting.\n"
                       "Changes are saved immediately (no .env edit needed)."),
    "settings_updated": "✅ Updated {key} → {value}",
    "settings_cleared": "✅ Cleared {key}",
    "settings_usage": "❌ Usage: /set_setting <key> <value>\nKeys: CHANNEL_ID, CHANNEL_LINK, WEBSITE_URL, SUPPORT_URL\nSend an empty value to clear a setting.",
    "settings_bad_key": "❌ Unknown setting: {key}. Use /settings to see valid keys.",
    # --- owner link management (website / support / channel) ---
    "link_menu_title": "🔗 {label} — current: {value}",
    "link_menu_none": "🔗 {label} — not set yet.",
    "link_set_btn": "✏️ Set / change link",
    "link_open_btn": "🔗 Open link",
    "link_clear_btn": "🗑️ Clear link",
    "link_await_input": "✏️ Send the {label} link now (or /cancel to stop).",
    "link_saved": "✅ {label} updated → {value}",
    "link_cleared": "🗑️ {label} cleared.",
    "link_cancelled": "↩️ Link setup cancelled.",
    "support_required_reminder": (
        "⚠️ Setup notice (owner):\n\n"
        "Your **Support link** is not set yet. Manual crypto payments send the "
        "buyer's **Transaction Hash** to your Support/owner DM for verification. "
        "Please set it:\n\n"
        "   Tap 🎧 Support → ✏️ Set / change link\n"
        "   then enter your Telegram DM link, e.g. https://t.me/yourname\n\n"
        "Without it, the buyer's TXID won't reach you."
    ),
    "admin_help": ("🛠 Owner commands:\n\n"
                   "📊 /stats - member & revenue summary\n"
                   "📢 /broadcast <text> - message all subscribers\n"
                   "➕ /add_member <user_id> - grant paid access ({days} days)\n"
                   "🚫 /kick <user_id> - remove a member\n"
                   "🛒 /products - list products\n"
                   "➕ /add_product Name|price|days|kind - add a product\n"
                   "➖ /remove_product <id> - remove a product\n"
                   "📦 /set_deliver <id> <text> - set digital delivery text\n"
                   "💰 /set_price <usd> - change the default price (current run)\n"
                   "⚙️ /settings - show store settings (channel, website, support)\n"
                   "🔧 /set_setting <key> <value> - set a store setting (see /settings)"),
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
    "prod_added": "✅ Product added: {name} (${price:.2f}, {days} days, {kind}){disc}",
    "prod_removed": "🚫 Product removed: {name}",
    "prod_not_found": "⚠️ No product with id: {id}",
    "prod_usage_add": ("❌ Usage: /add_product <name> | <price> [| <days> [| <kind> [| <discount%>]]]\n"
                       "  Only name and price are required.\n"
                       "  kind = channel (VIP) or digital (send link) — default: channel\n"
                       "  days = access length, 0 for lifetime — default: 30\n"
                       "  discount = percent off the price, 0 or empty for none\n"
                       "  Example:\n"
                       "     /add_product VIP Year | 49.99 | 365 | channel\n"
                       "     /add_product Course | 19.99 | 0 | digital | 20"),
    "prod_usage_remove": "❌ Usage: /remove_product <id>",
    "prod_need_desc": "For a digital product, set its delivery text with /set_deliver <id> <text>.",

    # --- add-product wizard (step by step) ---
    "wiz_category": ("📂 Step 1/5 — category\n\n"
                     "What category does this product belong to?\n"
                     "Examples: channel, digital, course, tool, ebook, ...\n"
                     "This groups similar products together in the shop."),
    "wiz_name": ("📝 Step 2/6 — name\n\n"
                 "Send the product NAME. This field is required."),
    "wiz_model": ("🏷️ Step 3/6 — model (optional)\n\n"
                  "Send a model, variant, or type for this product.\n"
                  "Examples: Men, Women, iPhone 17 Pro Max, Basic, Pro, ...\n"
                  "Leave empty / tap Skip for no model."),
    "wiz_price": ("💰 Step 4/6 — price\n\n"
                  "Send the PRICE in USD (e.g. 29.99). This field is required."),
    "wiz_days": ("⏳ Step 5/6 — access length (optional)\n\n"
                 "Send the number of DAYS, or 0 for lifetime.\n"
                 "Leave empty / tap Skip for the default (30 days)."),
    "wiz_discount": ("🏷️ Step 6/6 — discount % (optional)\n\n"
                     "Send a percent off the price, e.g. 20 for 20% off.\n"
                     "Leave empty / tap Skip for no discount."),
    "wiz_invalid_price": "❌ \"{hint}\" is not a valid price. Send a number like 29.99.",
    "wiz_invalid_days": "❌ \"{hint}\" is not a valid day count. Send 0, 30, 365, ...",
    "wiz_invalid_discount": "❌ \"{hint}\" is not a valid discount. Send a percent 0-99.",
    "wiz_incomplete": "⚠️ Product not added — missing a name or price. Start again with Add Product.",
    "wizard_cancelled": "Add product cancelled.",
    "wizard_skipped": "Skipped (using defaults).",
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
    "owner_remove_title": "🗑️ Tap a product to remove it:",
    "owner_confirm_remove": "⚠️ Remove \"{name}\"?",
    "owner_menu_updated": "✅ Menu updated.",
    "owner_menu_hidden_note": "(hidden buttons show dimmed below)",
    "delivery_set": "✅ Delivery text set for {name}.",
    "err_format": "❌ {msg}",
    "send_txid": (
        "⏳ Almost done!\n\n"
        "You paid via crypto. Now please send your "
        "**Transaction Hash (TXID)** so we can verify the payment.\n\n"
        "👉 Your transaction hash is the long ID you see in your wallet "
        "or the blockchain explorer after sending the coins.\n"
        "It usually looks like: 0x4f2a8b... or f9a2...\n\n"
        "Please paste it below:"
    ),
    "send_txid_hint": (
        "📎 How to find your Transaction Hash (TXID):\n\n"
        "🔹 In a crypto wallet (Trust Wallet / MetaMask / Safepal):\n"
        "   1. Open the app and tap the wallet you sent from.\n"
        "   2. Tap HISTORY or ACTIVITY, then open the transaction.\n"
        "   3. Tap 'TxID' / 'Hash' and copy it.\n\n"
        "🔹 In an exchange (Binance / Bybit):\n"
        "   1. Go to Withdraw > History.\n"
        "   2. Open the withdrawal and copy the TXID.\n\n"
        "🔹 On a block explorer (BscScan / Etherscan):\n"
        "   1. Paste your wallet address and find the outgoing transaction.\n"
        "   2. Copy its Transaction Hash (starts with 0x).\n\n"
        "It looks like a long string: 0x4f2a8b91c7e5a1b2c3d4e5f6a7b8c9d0e1f2a3b4\n\n"
        "👉 Paste it directly here in the chat."
    ),
    "txt_received": "✅ TXID received! Our team will verify it shortly. For manual crypto payments you will be granted access after confirmation.",
    "txid_owner_notify": "🧾 New manual payment — please verify:\n\n"
                         "👤 Buyer: {user}\n"
                         "📦 Product: {name}\n"
                         "💰 Amount: ${price:.2f}\n"
                         "⏰ Time: {time}\n"
                         "🔗 TXID: {txid}\n\n"
                         "Verify on the blockchain, then grant access.",
    "account_title": "👤 Your Account Information\n\n📅 Membership date: {since}\n🆔 Your ID: {uid}\n\n📊 Your transactions:\n\n📈 Total transactions: {txn_count}\n\n💰 Total payments:\n{payments}\n",

    "subscription_join": "🔔 You joined! Join the official channel here:\n{link}\n\nIf the link does not open, contact support.",
        "subscription_contact_support": "🔔 The channel link is not set yet. Contact support to get access:\n{link}",
        "subscription_not_ready": "🔔 Subscription channel is not configured yet. Please check back later.",
        "website_open": "🌐 Official website:\n{url}",
        "website_missing": "🌐 The owner has not set a website yet.",
        "support_open": "🎧 Contact support:\n{url}",
        "support_missing": "🎧 The owner has not set a support contact yet.",
    "np_check_status": "✅ Payment started with NOWPayments. Tap the button below to check it has been confirmed - no transaction hash is needed here.",
    "sale_notification": "🛎️ NEW SALE!\n\n🛒 Product: {name}\n💰 Price: ${price:.2f}\n👤 Buyer: {user}\n💳 Method: {method}\n🕐 {time}\n🔗 TXID: {txid}",
}


# ---------------------------------------------------------------------------
#  Button / keyboard labels
# ---------------------------------------------------------------------------
BTN = {
    "shop": "🛒 Shop / Products",
    "free_sub": "🔔 Subscription",
    "status": "📊 My Status",
    "help": "❓ Help",
    "website": "🌐 Official Website",
    "support": "🎧 Support",
    "account": "👤 My Account",
    "back_menu": "◀️ Back to menu",
    "back_shop": "◀️ Back to shop",
    "pay_nowpayments": "⭐ Recommended — Pay with Card / Crypto",
    "open_payment": "🔗 Open payment page",
    "pay_coingate": "🌐 Pay online (web page)",
    "pay_done": "✅ I paid",
    "check_payment": "🔎 Check payment status",
    "recommended_bsc": "⭐ {name} (Recommended)",
    "owner_manage": "⚙️ Owner Menu",
    "owner_add_product": "➕ Add Product",
    "owner_list_products": "🛒 List Products",
    "owner_howto_add": "❓ How to add",
    "owner_remove_product": "🗑️ Remove Product",
    "owner_confirm_yes": "✅ Yes, remove",
    "owner_confirm_no": "❌ Cancel",
    "wizard_cancel": "❌ Cancel",
    "wizard_skip": "⏭️ Skip",
    "wizard_back": "◀️ Back",
    "back": "◀️ Back",
    "link_set": "✏️ Set / change link",
    "link_open": "🔗 Open link",
    "link_clear": "🗑️ Clear link",
}


# ---------------------------------------------------------------------------
#  Product helpers (button labels & callbacks, driven by config.PRODUCTS)
# ---------------------------------------------------------------------------
def link_label(key):
    """Human-friendly label for a link setting key (WEBSITE_URL / SUPPORT_URL / CHANNEL_LINK)."""
    return {
        "WEBSITE_URL": "Website",
        "SUPPORT_URL": "Support contact",
        "CHANNEL_LINK": "Channel",
    }.get(key, key)


def link_hint(key):
    """Short guidance shown to the owner about what link to paste for a setting."""
    return {
        "WEBSITE_URL": "ℹ️ Enter your store/site URL, e.g. https://myshop.com",
        "SUPPORT_URL": "ℹ️ Enter a support link, e.g. your Telegram DM: https://t.me/yourname",
        "CHANNEL_LINK": "ℹ️ Enter your channel invite link, e.g. https://t.me/yourchannel",
    }.get(key, "")


def product_button(p):
    """Short button label for a product dict from config.PRODUCTS.
    Shows name + model (if set) + effective (post-discount) price."""
    import config  # local import to avoid lang<->config cycle
    price = config.effective_price(p)
    model = (p.get("model") or "").strip()
    name = p["name"]
    if model:
        name = f"{name} · {model}"
    return f"{p.get('emoji', TXT['emoji_default'])} {name} — ${price:.2f}"


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
