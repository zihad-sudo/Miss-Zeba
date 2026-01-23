import telebot
import html
import json
import os
import io
import traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.utils import get_text, set_text, get_data, reload_data, CUSTOM_FILE, send_backup, load_users

# ✅ প্লাগিন ম্যানেজারের ফাংশন ইমপোর্ট (ফোল্ডার ক্রিয়েশন লজিক)
try:
    from handlers.plugin_manager import initiate_add_tool
except ImportError:
    initiate_add_tool = None

# ডিফল্ট মেনু স্ট্রাকচার (যদি ডাটাবেসে না থাকে)
DEFAULT_STRUCTURE = {
    "main_menu": [ 
        ["🛠 Tools", "tools"], 
        ["🛒 Marketplace", "shop"], 
        ["💼 My Business", "my_business"] 
    ]
}

# =================================================
# 🖥️ ADMIN PANEL UI (ইন্টারফেস)
# =================================================
def send_admin_panel(bot, chat_id):
    structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
    kb = InlineKeyboardMarkup(row_width=1)
    
    # ১. ডায়নামিক মেনু ক্যাটাগরি (Menu Editing)
    for category_key in structure.keys():
        label = category_key.replace("_", " ").title()
        kb.add(InlineKeyboardButton(f"📂 Edit Menu: {label}", callback_data=f"adm_cat_{category_key}"))
    
    # ২. ফিক্সড টুলস (Broadcast & Analytics)
    kb.add(InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast"))
    kb.add(InlineKeyboardButton("📊 Analytics & Users", callback_data="adm_analytics"))
    
    # ✅ ৩. নতুন ফিচার: প্লাগিন টুল তৈরি করার বাটন
    kb.add(InlineKeyboardButton("➕ Create New Tool (Plugin)", callback_data="adm_create_tool"))

    # ৪. সেটিংস ব্যাকআপ ও রিস্টোর
    kb.add(
        InlineKeyboardButton("⬇️ Backup Settings", callback_data="adm_backup_dl"),
        InlineKeyboardButton("⬆️ Restore Settings", callback_data="adm_backup_ul")
    )
    
    # ৫. ক্লোজ বাটন
    kb.add(InlineKeyboardButton("❌ Close", callback_data="adm_close"))
    
    bot.send_message(chat_id, "👮 <b>Admin Panel</b>\n\nSelect an option to manage:", reply_markup=kb)

# =================================================
# 🎮 HANDLERS REGISTRATION (লজিক)
# =================================================
def register_admin_handlers(bot):
    
    # হেল্পার: এরর হ্যান্ডলিং (যাতে প্যানেল ক্র্যাশ না করে)
    def safe_run(call, func):
        try:
            bot.answer_callback_query(call.id)
            func()
        except Exception as e:
            print(f"❌ Admin Panel Error: {e}")
            try: bot.answer_callback_query(call.id, "❌ Error Occurred", show_alert=True)
            except: pass

    # --- ১. প্যানেল ওপেন করা ---
    @bot.callback_query_handler(func=lambda c: c.data in ["admin", "admin_panel", "main_btn_admin"])
    def open_admin_panel_handler(call):
        safe_run(call, lambda: send_admin_panel(bot, call.message.chat.id))

    # =================================================
    # ✅ ২. নতুন প্লাগিন টুল তৈরি হ্যান্ডলার
    # =================================================
    @bot.callback_query_handler(func=lambda c: c.data == "adm_create_tool")
    def handle_tool_creation(call):
        def action():
            if initiate_add_tool:
                # প্লাগিন ম্যানেজার কল করা হচ্ছে (নাম চাওয়ার জন্য)
                initiate_add_tool(bot, call.message.chat.id, call.from_user.id)
            else:
                bot.answer_callback_query(call.id, "⚠️ Plugin Manager missing!", show_alert=True)
        safe_run(call, action)

    # --- ৩. এনালাইটিক্স এবং ইউজার লিস্ট ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_analytics")
    def show_analytics(call):
        def action():
            users = load_users()
            text = f"📊 <b>Bot Analytics</b>\n\n👤 <b>Total Users:</b> {len(users)}"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📜 Download User List (.txt)", callback_data="adm_export_users"))
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=kb)
        safe_run(call, action)

    # --- ৪. ইউজার এক্সপোর্ট (Text File) ---
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
            bot.send_document(call.message.chat.id, file_obj, caption="✅ User List Export")
        safe_run(call, action)

    # --- ৫. ব্যাকআপ ডাউনলোড ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_dl")
    def download_backup(call):
        def action():
            if os.path.exists(CUSTOM_FILE):
                with open(CUSTOM_FILE, 'rb') as f:
                    bot.send_document(call.message.chat.id, f, caption="✅ Settings Backup (custom_data.json)", visible_file_name="custom_data.json")
            else:
                bot.answer_callback_query(call.id, "❌ File not found.")
        safe_run(call, action)

    # --- ৬. ব্যাকআপ রিস্টোর (আপলোড) ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_backup_ul")
    def ask_for_upload(call):
        def action():
            msg = bot.send_message(call.message.chat.id, "⬆️ <b>Upload your 'custom_data.json' file now.</b>\n\nThis will overwrite current settings.")
            bot.register_next_step_handler(msg, process_backup_upload, bot)
        safe_run(call, action)

    # --- ৭. ডায়নামিক মেনু এডিটিং ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_"))
    def open_category(call):
        def action():
            cat = call.data.replace("adm_cat_", "")
            structure = get_data("admin_menu_structure", DEFAULT_STRUCTURE)
            kb = InlineKeyboardMarkup(row_width=1)
            # ওই ক্যাটাগরির সব বাটন দেখানো
            for label, key in structure.get(cat, []):
                kb.add(InlineKeyboardButton(label, callback_data=f"adm_edit_{key}"))
            kb.add(InlineKeyboardButton("🔙 Back", callback_data="adm_home"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"📂 <b>Editing: {cat}</b>\nSelect an item to rename:", reply_markup=kb)
        safe_run(call, action)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_"))
    def edit_item(call):
        def action():
            key = call.data.replace("adm_edit_", "")
            val = get_text(key, "Not Set")
            msg = bot.send_message(call.message.chat.id, f"✏️ <b>Current Text:</b>\n<code>{val}</code>\n\n👇 <b>Send New Value:</b>")
            bot.register_next_step_handler(msg, process_new_text, bot, key)
        safe_run(call, action)

    # --- ৮. নেভিগেশন ---
    @bot.callback_query_handler(func=lambda c: c.data == "adm_home")
    def go_home(call):
        safe_run(call, lambda: (bot.delete_message(call.message.chat.id, call.message.message_id), send_admin_panel(bot, call.message.chat.id)))

    @bot.callback_query_handler(func=lambda c: c.data == "adm_close")
    def close_panel(call):
        safe_run(call, lambda: bot.delete_message(call.message.chat.id, call.message.message_id))

# --- PROCESS FUNCTIONS (নেক্সট স্টেপ হ্যান্ডলার) ---

def process_backup_upload(message, bot):
    if not message.document: 
        return bot.reply_to(message, "❌ Operation Cancelled (Not a file).")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        # JSON ভ্যালিডেশন
        json_data = json.loads(downloaded)
        
        with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        
        reload_data() # মেমোরিতে নতুন ডাটা লোড
        bot.reply_to(message, "✅ Settings Restored Successfully!")
        send_admin_panel(bot, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"❌ Restore Failed: {e}")

def process_new_text(message, bot, key):
    if not message.text: return
    if set_text(key, message.text, bot=bot, commit_msg=f"Updated {key}"):
        bot.reply_to(message, "✅ Text Updated!")
    else:
        bot.reply_to(message, "❌ Save Failed.")
    send_admin_panel(bot, message.chat.id)
