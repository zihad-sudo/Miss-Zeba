# keyboards/main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_text, is_admin

def main_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    
    # Standard Buttons
    btn_tools = InlineKeyboardButton(get_text("main_btn_tools", "🛠 Tools"), callback_data="tools")
    btn_shop = InlineKeyboardButton(get_text("main_btn_shop", "🛒 Shop"), callback_data="shop")
    btn_manager = InlineKeyboardButton(get_text("main_btn_manager", "📢 Manager"), callback_data="manager")

    kb.row(btn_tools, btn_shop)

    # Admin Button (Only visible if admin)
    if is_admin(user_id):
        btn_admin = InlineKeyboardButton(get_text("main_btn_admin", "👮 Admin"), callback_data="admin")
        kb.add(btn_admin)

    kb.add(btn_manager)
    return kb

def get_tools_layout():
    message_text = get_text("tools_message", "Select a tool:")
    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton(get_text("btn_speed", "🚀 Speed Test"), callback_data="tool_speed"),
        InlineKeyboardButton(get_text("btn_url", "🔗 Url Shortener"), callback_data="tool_url")
    )
    kb.row(
        InlineKeyboardButton(get_text("btn_dl", "📥 Downloader"), callback_data="tool_dl"),
        InlineKeyboardButton(get_text("btn_img", "🎨 Image Editor"), callback_data="tool_img")
    )
    kb.add(
        InlineKeyboardButton(get_text("btn_weather", "🌤 Weather"), callback_data="tool_weather")
    )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu_return"))
    
    return message_text, kb
