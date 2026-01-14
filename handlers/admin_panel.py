import telebot
import html
import json
import os
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.utils import get_text, set_text, get_data, reload_data, CUSTOM_FILE, send_backup, load_users

DEFAULT_STRUCTURE = {
    "main_menu": [ ["🔘 Edit Tools Button", "main_btn_tools"] ]
}

def send_admin_panel(bot, chat_id):
    structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
    kb = InlineKeyboardMarkup(row_width=1)
    
    for category_key in structure.keys():
        label = category_key.replace("_", " ").title()
        kb.add(InlineKeyboardButton(f"📂 {label}", callback_data=f"adm_cat_{category_key}"))
    
    # Broadcast (Handled in handlers/broadcast.py now)
    kb.add(InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast"))

    kb.add(InlineKeyboardButton("📊 Analytics & Users", callback_data="adm_analytics"))

    kb.add(
        InlineKeyboardButton("⬇️ Backup Settings", callback_data="adm_backup_dl"),
        InlineKeyboardButton("⬆️ Restore Settings", callback_data="adm_backup_ul")
    )
    kb.add(InlineKeyboardButton("❌ Close", callback_data="adm_close"))
    
    bot.send_message(chat_id, "👮 <b>Admin Panel</b>\n\nSelect an option:", reply_markup=kb)

def register_admin_handlers(bot):
    
    # --- ANALYTICS ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_analytics")
    def show_analytics(call):
        users = load_users()
        total_users = len(users)
        text = f"📊 <b>Bot Analytics</b>\n\n👤 <b>Total Users:</b> {total_users}\n<i>(Data sourced from users.json)</i>"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📜 Download User List (.txt)", callback_data="adm_export_users"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_export_users")
    def export_users(call):
        users = load_users()
        if not users:
            bot.answer_callback_query(call.id, "❌ No users found yet.")
            return
        output = "USER ID | NAME | USERNAME | LAST ACTIVE\n" + "="*45 + "\n"
        for uid, udata in users.items():
            name = udata.get("first_name", "Unknown")
            username = udata.get("username", "None")
            output += f"{uid} | {name} | @{username}\n"
        file_obj = io.BytesIO(output.encode('utf-8'))
        file_obj.name = "user_list.txt"
        bot.send_document(call.message.chat.id, file_obj, caption=f"✅ <b>User List Export</b>\nTotal: {len(users)}")

    # --- BACKUP & RESTORE ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_dl")
    def download_backup(call):
        chat_id = call.message.chat.id
        if os.path.exists(CUSTOM_FILE):
            with open(CUSTOM_FILE, 'rb') as f:
                bot.send_document(chat_id, f, caption="✅ <b>Settings Backup</b>", visible_file_name="custom_data.json")
        else:
            bot.answer_callback_query(call.id, "❌ No data found.", show_alert=True)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_ul")
    def ask_for_upload(call):
        msg = bot.send_message(call.message.chat.id, "⬆️ <b>Upload Settings</b>\nSend custom_data.json now.")
        bot.register_next_step_handler(msg, process_backup_upload, bot)

    # --- DYNAMIC CATEGORIES ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_"))
    def open_category(call):
        category = call.data.replace("adm_cat_", "")
        structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
        items_list = structure.get(category, [])
        kb = InlineKeyboardMarkup(row_width=1)
        for label, key_id in items_list:
            kb.add(InlineKeyboardButton(label, callback_data=f"adm_edit_{key_id}"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"📂 <b>Editing: {category}</b>", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_"))
    def edit_item(call):
        key = call.data.replace("adm_edit_", "")
        raw_text = get_text(key, "Not Set")
        safe_display_text = html.escape(raw_text)
        msg = bot.send_message(call.message.chat.id, f"✏️ <b>Editing:</b> <code>{key}</code>\n\n<b>Current:</b>\n<code>{safe_display_text}</code>\n\n👇 <b>Send NEW text:</b>")
        bot.register_next_step_handler(msg, process_new_text, bot, key)

    # --- NAVIGATION ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_home")
    def go_home(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_admin_panel(bot, call.message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_close")
    def close_panel(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)

# --- PROCESS FUNCTIONS ---
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
        send_backup(bot, commit_msg="Manual Settings Restore")
        bot.reply_to(message, "✅ Settings Restored!")
        send_admin_panel(bot, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def process_new_text(message, bot, key):
    new_text = message.text
    if not new_text:
        bot.send_message(message.chat.id, "❌ Text only.")
        return
    readable_name = key.replace('_', ' ').title()
    commit_msg = f"{readable_name} Update"
    if set_text(key, new_text, bot=bot, commit_msg=commit_msg):
        safe_text = html.escape(new_text)
        bot.send_message(message.chat.id, f"✅ Saved:\n<code>{safe_text}</code>")
    else:
        bot.send_message(message.chat.id, "❌ Error saving.")
    send_admin_panel(bot, message.chat.id)
