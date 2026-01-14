from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.utils import get_text, is_admin

# -------------------------------
# Main Menu
# -------------------------------
def main_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton("🛠 Tools", callback_data="tools"),
        InlineKeyboardButton("🛒 Marketplace", callback_data="shop")
    )
    kb.add(InlineKeyboardButton("💼 My Business", callback_data="my_business"))
    if is_admin(user_id):
        kb.add(InlineKeyboardButton("👮 Admin", callback_data="admin"))
    kb.add(InlineKeyboardButton("📢 Manager", callback_data="manager"))
    return kb

# -------------------------------
# Tools menu
# -------------------------------
def tools_layout():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🚀 Speed Test", callback_data="tool_speed"),
        InlineKeyboardButton("🔗 URL Shortener", callback_data="tool_url_shortener")
    )
    kb.row(
        InlineKeyboardButton("📥 Downloader", callback_data="tool_dl"),
        InlineKeyboardButton("🎨 Image Editor", callback_data="tool_img")
    )
    kb.add(InlineKeyboardButton("🌤 Weather", callback_data="tool_weather"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu_return"))
    return "Select a tool:", kb

# -------------------------------
# URL Shortener menu (shows emoji/QR state)
# -------------------------------
def tool_url_shorten_menu(chat_id, state):
    """
    state: {"emoji": True/False, "qr": True/False}
    """
    message_text = "Send the URL to shorten or customize:"
    kb = InlineKeyboardMarkup()

    emoji_text = "✅ Emoji Mode ON" if state.get("emoji", True) else "❌ Emoji Mode OFF"
    qr_text = "✅ QR Mode ON" if state.get("qr", True) else "❌ QR Mode OFF"

    kb.row(
        InlineKeyboardButton(emoji_text, callback_data="toggle_emoji"),
        InlineKeyboardButton(qr_text, callback_data="toggle_qr")
    )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="tools"))
    return message_text, kb
