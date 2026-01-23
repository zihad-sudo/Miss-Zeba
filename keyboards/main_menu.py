from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Utils ইম্পোর্ট করার চেষ্টা, না পেলে ডিফল্ট ভ্যালু
try:
    from utils.utils import get_text, is_admin
except ImportError:
    # যদি utils না থাকে তবে এই ফাংশনগুলো কাজ করবে
    def is_admin(user_id): return False
    def get_text(text): return text

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
    
    # Admin চেক
    if is_admin(user_id):
        kb.add(InlineKeyboardButton("👮 Admin", callback_data="admin"))
    
    kb.add(InlineKeyboardButton("📢 Manager", callback_data="manager"))
    return kb

# -------------------------------
# Tools menu (Updated)
# -------------------------------
def tools_layout():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🔥 Auto Save", url="https://t.me/MissZeba_Auto_Save_Bot"),
        InlineKeyboardButton("🔗 URL Shortener", callback_data="tool_url_shortener")
    )
    kb.row(
        InlineKeyboardButton("🛡️ Group Manage", callback_data="open_management"),
        InlineKeyboardButton("🎨 Watermark Studio", callback_data="tool_img")
    )
    kb.add(InlineKeyboardButton("🌤 Weather", callback_data="tool_weather"))
    
    # মেইন মেনু রিটার্ন বাটন
    kb.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu_return"))
    
    return "🛠 **Select a Tool:**", kb
