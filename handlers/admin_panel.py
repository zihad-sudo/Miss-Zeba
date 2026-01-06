# handlers/admin_panel.py
import telebot
import html
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_text, set_text, get_data, reload_data, CUSTOM_FILE, send_backup

DEFAULT_STRUCTURE = {
    "main_menu": [ ["🔘 Edit Tools Button", "main_btn_tools"] ]
}

def send_admin_panel(bot, chat_id):
    structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
    kb = InlineKeyboardMarkup(row_width=1)
    
    for category_key in structure.keys():
        label = category_key.replace("_", " ").title()
        kb.add(InlineKeyboardButton(f"📂 {label}", callback_data=f"adm_cat_{category_key}"))
    
    kb.add(
        InlineKeyboardButton("⬇️ Download Backup", callback_data="adm_backup_dl"),
        InlineKeyboardButton("⬆️ Upload Backup", callback_data="adm_backup_ul")
    )
    kb.add(InlineKeyboardButton("❌ Close", callback_data="adm_close"))
    
    bot.send_message(chat_id, "👮 <b>Admin Panel</b>\n\nSelect an option:", reply_markup=kb)

def register_admin_handlers(bot):
    
    # --- Backup Download ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_dl")
    def download_backup(call):
        chat_id = call.message.chat.id
        if os.path.exists(CUSTOM_FILE):
            with open(CUSTOM_FILE, 'rb') as f:
                bot.send_document(chat_id, f, caption="✅ <b>Backup File</b>", visible_file_name="custom_data.json")
        else:
            bot.answer_callback_query(call.id, "❌ No data found.", show_alert=True)

    # --- Backup Upload ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_ul")
    def ask_for_upload(call):
        msg = bot.send_message(call.message.chat.id, "⬆️ <b>Upload Backup</b>\nSend the JSON file now.")
        bot.register_next_step_handler(msg, process_backup_upload, bot)

    # --- Categories ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_"))
    def open_category(call):
        category = call.data.replace("adm_cat_", "")
        structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
        items_list = structure.get(category, [])
        
        kb = InlineKeyboardMarkup(row_width=1)
        for label, key_id in items_list:
            kb.add(InlineKeyboardButton(label, callback_data=f"adm_edit_{key_id}"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📂 <b>Editing: {category.replace('_', ' ').title()}</b>",
            reply_markup=kb
        )

    # --- Edit Item ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_"))
    def edit_item(call):
        key = call.data.replace("adm_edit_", "")
        raw_text = get_text(key, "Not Set")
        safe_display_text = html.escape(raw_text)
        
        msg = bot.send_message(
            call.message.chat.id,
            f"✏️ <b>Editing:</b> <code>{key}</code>\n\n<b>Current:</b>\n<code>{safe_display_text}</code>\n\n👇 <b>Send NEW text:</b>"
        )
        bot.register_next_step_handler(msg, process_new_text, bot, key)

    # --- Navigation ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_home")
    def go_home(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_admin_panel(bot, call.message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_close")
    def close_panel(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)

def process_backup_upload(message, bot):
    if not message.document:
        bot.reply_to(message, "❌ Not a file.")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        json_content = json.loads(downloaded_file)
        
        with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=4, ensure_ascii=False)
        reload_data()
        send_backup(bot)
        bot.reply_to(message, "✅ Backup Restored!")
        send_admin_panel(bot, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def process_new_text(message, bot, key):
    new_text = message.text
    if not new_text:
        bot.send_message(message.chat.id, "❌ Text only.")
        return
    if set_text(key, new_text, bot=bot):
        safe_text = html.escape(new_text)
        bot.send_message(message.chat.id, f"✅ Saved:\n<code>{safe_text}</code>")
    else:
        bot.send_message(message.chat.id, "❌ Error saving.")
    send_admin_panel(bot, message.chat.id)
