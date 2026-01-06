from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🛠 Tools", callback_data="tools"),
        InlineKeyboardButton("🛒 Shop", callback_data="shop"),
        InlineKeyboardButton("👮 Admin", callback_data="admin"),
        InlineKeyboardButton("📢 Manager", callback_data="manager"),
    )
    return kb
