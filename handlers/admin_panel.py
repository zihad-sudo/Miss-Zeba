import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPER_ADMINS
from utils import get_text, set_text, get_data

# Fallback structure (Safety net if JSON is empty/broken)
DEFAULT_STRUCTURE = {
    "main_menu": [ ["🔘 Edit Tools Button", "main_btn_tools"] ]
}

def send_admin_panel(bot, chat_id):
    """
    Dynamically builds the Category Menu (Start, Main Menu, etc.)
    based on the keys found in 'admin_menu_structure'.
    """
    # 1. Fetch the structure dictionary
    structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    # 2. Create a button for each Category found in JSON
    # keys would be "start", "main_menu", "tools_menu"
    for category_key in structure.keys():
        # Make the button label look nice ("main_menu" -> "Main Menu")
        label = category_key.replace("_", " ").title()
        kb.add(InlineKeyboardButton(f"📂 {label}", callback_data=f"adm_cat_{category_key}"))
        
    kb.add(InlineKeyboardButton("❌ Close", callback_data="adm_close"))
    
    bot.send_message(chat_id, "👮 <b>Admin Panel</b>\n\nSelect a category to edit:", reply_markup=kb)

def register_admin_handlers(bot):
    
    # --- 1. Category Selection ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_"))
    def open_category(call):
        category = call.data.replace("adm_cat_", "")
        
        # Load structure again
        structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
        # Get the list of items for this category
        items_list = structure.get(category, [])
        
        kb = InlineKeyboardMarkup(row_width=1)
        
        # Iterate through [ "Button Name", "Key ID" ]
        for label, key_id in items_list:
            kb.add(InlineKeyboardButton(label, callback_data=f"adm_edit_{key_id}"))
        
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📂 <b>Editing: {category.replace('_', ' ').title()}</b>\nSelect an item:",
            reply_markup=kb
        )

    # --- 2. Edit Item Selection ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_"))
    def edit_item(call):
        key = call.data.replace("adm_edit_", "")
        current_text = get_text(key, "Not Set")
        
        msg = bot.send_message(
            call.message.chat.id,
            f"✏️ <b>Editing:</b> <code>{key}</code>\n\n"
            f"<b>Current Text:</b>\n{current_text}\n\n"
            f"👇 <b>Send the NEW text now:</b>\n"
            f"<i>(HTML tags allowed)</i>"
        )
        bot.register_next_step_handler(msg, process_new_text, bot, key)

    # --- 3. Navigation ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_home")
    def go_home(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_admin_panel(bot, call.message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_close")
    def close_panel(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)

def process_new_text(message, bot, key):
    """Background function to save text"""
    new_text = message.text
    
    if not new_text:
        bot.send_message(message.chat.id, "❌ Error: Only text is allowed.")
        return

    if set_text(key, new_text):
        bot.send_message(message.chat.id, f"✅ <b>Updated Successfully!</b>\n\nNew value for <code>{key}</code> saved.")
    else:
        bot.send_message(message.chat.id, "❌ Error saving file.")
    
    # Send user back to main panel
    send_admin_panel(bot, message.chat.id)
