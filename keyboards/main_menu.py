from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.utils import is_admin

# ✅ প্লাগিন হেল্পার (যাতে নতুন টুলসগুলো টুলস মেনুতে দেখা যায়)
try:
    from handlers.plugin_manager import get_dynamic_tools
except ImportError:
    def get_dynamic_tools(): return []

# =================================================
# 🏠 MAIN MENU (Original Fixed Layout)
# =================================================
def main_menu(user_id):
    """
    এটি ডাটাবেস থেকে মেনু লোড করবে না।
    সরাসরি ফিক্সড বাটন দেখাবে যাতে লেআউট নষ্ট না হয়।
    """
    kb = InlineKeyboardMarkup(row_width=2)
    
    # --- Row 1: Tools & Shop ---
    btn_tools = InlineKeyboardButton("🛠 Tools", callback_data="tools")
    btn_shop = InlineKeyboardButton("🛒 Marketplace", callback_data="shop")
    kb.add(btn_tools, btn_shop)
    
    # --- Row 2: Business ---
    btn_biz = InlineKeyboardButton("💼 My Business", callback_data="my_business")
    kb.add(btn_biz)
    
    # --- Row 3: Admin (Only for Admins) ---
    if is_admin(user_id):
        btn_admin = InlineKeyboardButton("👮 Admin Panel", callback_data="main_btn_admin")
        kb.add(btn_admin)

    return kb

# =================================================
# 🛠 TOOLS MENU (With Plugin Support)
# =================================================
def tools_layout():
    kb = InlineKeyboardMarkup(row_width=2)
    
    # --- 1. Built-in Tools (আপনার আগের ফিক্সড টুলস) ---
    # Row 1
    kb.add(
        InlineKeyboardButton("🔗 URL Shortener", callback_data="tool_url_shortener"),
        InlineKeyboardButton("🎨 Watermark", callback_data="tool_img")
    )
    # Row 2
    kb.add(
        InlineKeyboardButton("🛡️ Group Manage", callback_data="open_management"),
        InlineKeyboardButton("🌤 Weather", callback_data="tool_weather")
    )

    # --- 2. 🔌 DYNAMIC PLUGINS (নতুন আপলোড করা টুলস) ---
    dynamic_buttons = get_dynamic_tools()
    
    # বাটনগুলো সুন্দরভাবে ২ কলামে সাজানো
    temp_row = []
    for label, callback in dynamic_buttons:
        temp_row.append(InlineKeyboardButton(label, callback_data=callback))
        if len(temp_row) == 2:
            kb.row(*temp_row)
            temp_row = []
    if temp_row: kb.row(*temp_row)

    # --- 3. Navigation ---
    kb.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu_return"))
    
    return "🛠 **Tools Menu:**\nSelect a tool from below:", kb
