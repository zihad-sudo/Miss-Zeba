import os
import sys
import ast
import time
import importlib.util
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPER_ADMINS

PLUGIN_BASE_DIR = "handlers/plugins"

# ফোল্ডার নিশ্চিত করা
if not os.path.exists(PLUGIN_BASE_DIR):
    os.makedirs(PLUGIN_BASE_DIR)

# 🔒 STATE MANAGEMENT
# user_id: { 'step': 'name'/'upload', 'folder': 'xyz' }
CREATION_STATE = {}

def check_syntax(code_content):
    """পাইথন ফাইলের সিনট্যাক্স চেক করে"""
    try:
        ast.parse(code_content)
        return True, None
    except SyntaxError as e:
        return False, f"{e.msg} (Line {e.lineno})"
    except Exception as e:
        return False, str(e)

def restart_bot():
    """বট রিস্টার্ট"""
    print("🔄 Restarting bot to load new tools...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ==========================================
# 🚀 1. ENTRY POINT & STATES
# ==========================================

def initiate_add_tool(bot, chat_id, user_id):
    """Step 1: Ask for Folder Name"""
    CREATION_STATE[user_id] = {'step': 'waiting_name'}
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_plugin_creation"))
    
    bot.send_message(chat_id, 
                     "🛠 **Create New Tool**\n\n"
                     "Please send a short **Folder Name** for this tool.\n"
                     "(Example: `qr_maker`, `bg_remover`, `ai_chat`)\n\n"
                     "⚠️ *Use lowercase letters and underscores only.*", 
                     reply_markup=kb, parse_mode="Markdown")

def cancel_creation(bot, chat_id, user_id):
    if user_id in CREATION_STATE:
        del CREATION_STATE[user_id]
        bot.send_message(chat_id, "❌ Tool creation cancelled.")

# ==========================================
# 📥 2. HANDLERS (Folder & Files)
# ==========================================

def register_plugin_handler(bot):
    
    # --- A. CANCEL BUTTON ---
    @bot.callback_query_handler(func=lambda c: c.data == "cancel_plugin_creation")
    def handle_cancel(call):
        cancel_creation(bot, call.message.chat.id, call.from_user.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    # --- B. DONE BUTTON (Finish Upload) ---
    @bot.callback_query_handler(func=lambda c: c.data == "finish_plugin_upload")
    def handle_finish(call):
        user_id = call.from_user.id
        if user_id in CREATION_STATE and CREATION_STATE[user_id]['step'] == 'uploading':
            folder = CREATION_STATE[user_id]['folder']
            del CREATION_STATE[user_id]
            
            bot.edit_message_text(f"✅ **Setup Complete!**\n\nTool `{folder}` installed successfully.\n🔄 Restarting system to apply changes...", 
                                  call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            time.sleep(2)
            restart_bot()

    # --- C. TEXT HANDLER (For Folder Name) ---
    @bot.message_handler(func=lambda m: m.from_user.id in CREATION_STATE and CREATION_STATE[m.from_user.id]['step'] == 'waiting_name', content_types=['text'])
    def handle_folder_name(message):
        user_id = message.from_user.id
        raw_name = message.text.strip().lower()
        
        # Validating folder name
        safe_name = "".join(c for c in raw_name if c.isalnum() or c == "_")
        
        full_path = os.path.join(PLUGIN_BASE_DIR, safe_name)
        
        if os.path.exists(full_path):
            bot.reply_to(message, f"⚠️ A tool named `{safe_name}` already exists. Please choose a different name.")
            return
        
        # Create Folder
        try:
            os.makedirs(full_path)
            # Create __init__.py
            with open(os.path.join(full_path, "__init__.py"), 'w') as f:
                f.write("# Plugin Package")
            
            # Update State
            CREATION_STATE[user_id] = {'step': 'uploading', 'folder': safe_name}
            
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Done / Finish Upload", callback_data="finish_plugin_upload"))
            kb.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_plugin_creation"))
            
            bot.reply_to(message, 
                         f"📂 **Folder Created:** `{safe_name}`\n\n"
                         f"👉 Now send your `.py` files, images, or requirements.\n"
                         f"👉 Ensure one `.py` file has `TOOL_INFO` for the menu.\n\n"
                         f"Click **Done** when finished.", 
                         reply_markup=kb, parse_mode="Markdown")
            
        except Exception as e:
            bot.reply_to(message, f"❌ Error creating folder: {e}")

    # --- D. DOCUMENT HANDLER (File Upload) ---
    @bot.message_handler(content_types=['document'])
    def handle_files(message):
        user_id = message.from_user.id
        
        # Check if user is in uploading state
        if user_id not in CREATION_STATE or CREATION_STATE[user_id]['step'] != 'uploading':
            return 
        
        if user_id not in SUPER_ADMINS: return

        folder_name = CREATION_STATE[user_id]['folder']
        save_dir = os.path.join(PLUGIN_BASE_DIR, folder_name)
        
        doc = message.document
        file_name = doc.file_name
        
        msg = bot.reply_to(message, "⏳ Uploading...")
        
        try:
            file_info = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            # If python file, check syntax
            if file_name.endswith(".py"):
                is_valid, err = check_syntax(downloaded)
                if not is_valid:
                    bot.edit_message_text(f"❌ **Syntax Error in {file_name}:**\n`{err}`\nFile NOT saved.", message.chat.id, msg.message_id, parse_mode="Markdown")
                    return
            
            # Save File
            file_path = os.path.join(save_dir, file_name)
            with open(file_path, 'wb') as f:
                f.write(downloaded)
            
            bot.edit_message_text(f"✅ Saved: `{file_name}` inside `{folder_name}`", message.chat.id, msg.message_id, parse_mode="Markdown")
            
        except Exception as e:
            bot.edit_message_text(f"❌ Upload Failed: {e}", message.chat.id, msg.message_id)

# ==========================================
# 🛠 3. DYNAMIC MENU HELPER
# ==========================================
def get_dynamic_tools():
    """
    Plugin ফোল্ডার স্ক্যান করে এবং TOOL_INFO খুঁজে বের করে মেনুর জন্য।
    Returns list of [Label, Callback]
    """
    tools_list = []
    
    if not os.path.exists(PLUGIN_BASE_DIR): return []

    # প্রতিটি সাব-ফোল্ডার চেক করা
    for folder in os.listdir(PLUGIN_BASE_DIR):
        folder_path = os.path.join(PLUGIN_BASE_DIR, folder)
        
        if os.path.isdir(folder_path):
            # ফোল্ডারের ভেতর সব .py ফাইল চেক করা
            for file in os.listdir(folder_path):
                if file.endswith(".py"):
                    try:
                        # মডিউল লোড না করে টেক্সট পড়ে TOOL_INFO খোঁজা (Fast & Safe)
                        # অথবা ইমপোর্ট করা (More Reliable)
                        
                        module_name = f"handlers.plugins.{folder}.{file[:-3]}"
                        spec = importlib.util.spec_from_file_location(module_name, os.path.join(folder_path, file))
                        module = importlib.util.module_from_spec(spec)
                        
                        # আমরা এখানে পুরো এক্সিকিউট করব না, শুধু চেক করব
                        # কিন্তু TOOL_INFO ভ্যালু পেতে হলে এক্সিকিউট দরকার
                        spec.loader.exec_module(module)
                        
                        if hasattr(module, "TOOL_INFO"):
                            info = module.TOOL_INFO
                            # info format: {"label": "Name", "callback": "data"}
                            if "label" in info and "callback" in info:
                                tools_list.append([info["label"], info["callback"]])
                                break # একটা ফোল্ডারে একটা মেনু আইটেমই যথেষ্ট
                    except:
                        continue
    return tools_list
