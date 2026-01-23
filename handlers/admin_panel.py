import telebot
import html
import json
import os
import io
import traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.utils import get_text, set_text, get_data, reload_data, CUSTOM_FILE, send_backup, load_users

# ডিফল্ট মেনু স্ট্রাকচার
DEFAULT_STRUCTURE = {
    "main_menu": [ ["🔘 Edit Tools Button", "main_btn_tools"] ]
}

# =================================================
# 🖥️ ADMIN PANEL UI
# =================================================
def send_admin_panel(bot, chat_id):
    structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
    kb = InlineKeyboardMarkup(row_width=1)
    
    # ক্যাটাগরি বাটনগুলো ডাইনামিক্যালি তৈরি হবে
    for category_key in structure.keys():
        label = category_key.replace("_", " ").title()
        kb.add(InlineKeyboardButton(f"📂 {label}", callback_data=f"adm_cat_{category_key}"))
    
    # ফিক্সড বাটন
    kb.add(InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast"))
    kb.add(InlineKeyboardButton("📊 Analytics & Users", callback_data="adm_analytics"))
    kb.add(
        InlineKeyboardButton("⬇️ Backup Settings", callback_data="adm_backup_dl"),
        InlineKeyboardButton("⬆️ Restore Settings", callback_data="adm_backup_ul")
    )
    kb.add(InlineKeyboardButton("❌ Close", callback_data="adm_close"))
    
    bot.send_message(chat_id, "👮 <b>Admin Panel</b>\n\nSelect an option:", reply_markup=kb)

# =================================================
# 🎮 HANDLERS REGISTRATION
# =================================================
def register_admin_handlers(bot):
    
    # হেল্পার: এরর হ্যান্ডলিং এবং লোডিং স্টপ করা
    def safe_run(call, func):
        try:
            bot.answer_callback_query(call.id)
            func()
        except Exception as e:
            print(f"❌ Admin Panel Error: {e}")
            try: bot.answer_callback_query(call.id, "❌ Error Occurred", show_alert=True)
            except: pass

    # 🔥 CRITICAL FIX: Admin বাটন হ্যান্ডলার
    # আপনার custom_data.json এ বাটনের ডাটা "main_btn_admin" দেওয়া আছে।
    # তাই আমরা এখানে "admin", "admin_panel" এবং "main_btn_admin" সব চেক করছি।
    @bot.callback_query_handler(func=lambda c: c.data in ["admin", "admin_panel", "main_btn_admin"])
    def open_admin_panel_handler(call):
        safe_run(call, lambda: send_admin_panel(bot, call.message.chat.id))

    # --- ANALYTICS ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_analytics")
    def show_analytics(call):
        def action():
            users = load_users()
            text = f"📊 <b>Bot Analytics</b>\n\n👤 <b>Total Users:</b> {len(users)}"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📜 Download User List", callback_data="adm_export_users"))
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=kb)
        safe_run(call, action)

    # --- USER EXPORT ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_export_users")
    def export_users(call):
        def action():
            users = load_users()
            if not users:
                bot.answer_callback_query(call.id, "❌ No users found.", show_alert=True)
                return
            output = "ID | NAME | USERNAME\n" + "="*30 + "\n"
            for uid, udata in users.items():
                output += f"{uid} | {udata.get('first_name','?')} | @{udata.get('username','?')}\n"
            file_obj = io.BytesIO(output.encode('utf-8'))
            file_obj.name = "users.txt"
            bot.send_document(call.message.chat.id, file_obj, caption="✅ User List")
        safe_run(call, action)

    # --- BACKUP ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_dl")
    def download_backup(call):
        def action():
            if os.path.exists(CUSTOM_FILE):
                with open(CUSTOM_FILE, 'rb') as f:
                    bot.send_document(call.message.chat.id, f, caption="✅ Settings Backup", visible_file_name="custom_data.json")
            else:
                bot.answer_callback_query(call.id, "❌ File not found.")
        safe_run(call, action)

    # --- RESTORE ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_ul")
    def ask_for_upload(call):
        def action():
            msg = bot.send_message(call.message.chat.id, "⬆️ <b>Upload custom_data.json file now.</b>")
            bot.register_next_step_handler(msg, process_backup_upload, bot)
        safe_run(call, action)

    # --- DYNAMIC EDITING ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_"))
    def open_category(call):
        def action():
            cat = call.data.replace("adm_cat_", "")
            structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
            kb = InlineKeyboardMarkup(row_width=1)
            for label, key in structure.get(cat, []):
                kb.add(InlineKeyboardButton(label, callback_data=f"adm_edit_{key}"))
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"📂 <b>Editing: {cat}</b>", reply_markup=kb)
        safe_run(call, action)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_"))
    def edit_item(call):
        def action():
            key = call.data.replace("adm_edit_", "")
            val = get_text(key, "Not Set")
            msg = bot.send_message(call.message.chat.id, f"✏️ <b>Current:</b>\n<code>{val}</code>\n\n👇 <b>Send New Value:</b>")
            bot.register_next_step_handler(msg, process_new_text, bot, key)
        safe_run(call, action)

    # --- NAVIGATION ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_home")
    def go_home(call):
        safe_run(call, lambda: (bot.delete_message(call.message.chat.id, call.message.message_id), send_admin_panel(bot, call.message.chat.id)))

    @bot.callback_query_handler(func=lambda c: c.data == "adm_close")
    def close_panel(call):
        safe_run(call, lambda: bot.delete_message(call.message.chat.id, call.message.message_id))

# --- PROCESSOR FUNCTIONS ---
def process_backup_upload(message, bot):
    if not message.document: return bot.reply_to(message, "❌ Cancelled.")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
            json.dump(json.loads(downloaded), f, indent=4, ensure_ascii=False)
        reload_data()
        bot.reply_to(message, "✅ Settings Restored!")
        send_admin_panel(bot, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def process_new_text(message, bot, key):
    if not message.text: return
    if set_text(key, message.text, bot=bot, commit_msg=f"Updated {key}"):
        bot.reply_to(message, "✅ Saved!")
    else:
        bot.reply_to(message, "❌ Save Failed.")
    send_admin_panel(bot, message.chat.id)
