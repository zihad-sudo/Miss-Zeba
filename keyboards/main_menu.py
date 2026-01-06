from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_text

def main_menu():
    """
    Main Menu: Manual Layout
    """
    kb = InlineKeyboardMarkup()

    # --- Row 1: Tools & Shop (Side by Side) ---
    kb.row(
        InlineKeyboardButton(get_text("main_btn_tools", "🛠 Tools"), callback_data="tools"),
        InlineKeyboardButton(get_text("main_btn_shop", "🛒 Shop"), callback_data="shop")
    )

    # --- Row 2: Admin (Alone) ---
    kb.add(
        InlineKeyboardButton(get_text("main_btn_admin", "👮 Admin"), callback_data="admin")
    )

    # --- Row 3: Manager (Alone) ---
    kb.add(
        InlineKeyboardButton(get_text("main_btn_manager", "📢 Manager"), callback_data="manager")
    )
    
    return kb

def get_tools_layout():
    """
    Tools Menu: Manual Layout
    """
    message_text = get_text("tools_message", "Select a tool:")
    
    kb = InlineKeyboardMarkup()

    # --- Row 1: Speed & URL (Side by Side) ---
    kb.row(
        InlineKeyboardButton(get_text("btn_speed", "🚀 Speed Test"), callback_data="tool_speed"),
        InlineKeyboardButton(get_text("btn_url", "🔗 Url Shortener"), callback_data="tool_url")
    )

    # --- Row 2: Downloader & Image (Side by Side) ---
    kb.row(
        InlineKeyboardButton(get_text("btn_dl", "📥 Downloader"), callback_data="tool_dl"),
        InlineKeyboardButton(get_text("btn_img", "🎨 Image Editor"), callback_data="tool_img")
    )

    # --- Row 3: Weather (Alone) ---
    kb.add(
        InlineKeyboardButton(get_text("btn_weather", "🌤 Weather"), callback_data="tool_weather")
    )

    # --- Row 4: Back Button ---
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu_return"))
    
    return message_text, kb
