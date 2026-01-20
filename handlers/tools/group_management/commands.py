import time
import threading
import os
from telebot import types
from .data import get_data
from .utils import is_admin
from .logic import perform_action, handle_warning

# =========================================================
# 👇 IMPORT AREA (Tools Engines)
# =========================================================

# 1. URL Shortener (FIXED IMPORT PATH)
try:
    # 🔥 ফোল্ডার নয়, সরাসরি ফাইলের নাম (.url_shorten) উল্লেখ করা হয়েছে
    from handlers.tools.url_shorten.url_shorten import process_url
    URL_SHORTENER_AVAILABLE = True
except ImportError:
    # যদি আপনি ফাইলের নাম core.py দিয়ে থাকেন, তবে এটি কাজ করবে
    try:
        from handlers.tools.url_shorten.core import process_url
        URL_SHORTENER_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ URL Shortener Error: {e}")
        URL_SHORTENER_AVAILABLE = False


# 2. Watermark Engine & Data (Global Source)
try:
    from handlers.tools.watermark.engine import apply_watermark_image, apply_watermark_video
    from handlers.tools.watermark.data import get_wm_settings
except ImportError:
    apply_watermark_image = None
    apply_watermark_video = None
    get_wm_settings = None
    print("⚠️ Watermark Tool module not found.")

# =========================================================
# CONSTANTS
# =========================================================
# File Size Limit (20 MB - Telegram Bot Default Limit)
MAX_WM_SIZE = 20 * 1024 * 1024 

def register_commands(bot):
    
    # ---------------------------------------------
    # 🔥 GHOST MODE HELPER (Auto-Delete System)
    # ---------------------------------------------
    def reply_temp(message, text, delay=5):
        """Sends a reply and auto-deletes it after 'delay' seconds."""
        try:
            # 1. Send Reply
            sent_msg = bot.reply_to(message, text, parse_mode="Markdown")
            
            # 2. Start Background Thread for Deletion
            def run_delete():
                time.sleep(delay) # Wait
                try:
                    bot.delete_message(message.chat.id, message.message_id)   # Delete User Command
                    bot.delete_message(message.chat.id, sent_msg.message_id)  # Delete Bot Reply
                except:
                    pass 

            threading.Thread(target=run_delete).start()
        except Exception as e:
            print(f"Error in ghost reply: {e}")

    # ---------------------------------------------
    # 1. GROUP TOOLS COMMANDS
    # ---------------------------------------------

    # --- A. WATERMARK TOOL (/wm) ---
    @bot.message_handler(commands=['wm', 'watermark'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_tool_wm(m):
        # Module Check
        if apply_watermark_image is None:
            reply_temp(m, "⚠️ Watermark module missing.")
            return

        # 1. Check if Tool is Enabled in Group
        group_data = get_data(m.chat.id)
        if not group_data['tools']['watermark']: return

        # 2. Check Reply and File Type
        reply = m.reply_to_message
        if not reply:
            reply_temp(m, "⚠️ Reply to a Photo, Video, or GIF with `/wm`.")
            return

        file_type = None
        if reply.photo: file_type = 'photo'
        elif reply.video: file_type = 'video'
        elif reply.animation: file_type = 'gif'
        else:
            reply_temp(m, "⚠️ Only Photo, Video, or GIF are supported.")
            return

        msg = bot.reply_to(m, f"⏳ Processing {file_type.title()}...")

        try:
            # 3. Get File Info & Size Check
            if file_type == 'photo': file_id = reply.photo[-1].file_id
            elif file_type == 'video': file_id = reply.video.file_id
            elif file_type == 'gif': file_id = reply.animation.file_id

            file_info = bot.get_file(file_id)
            
            if file_info.file_size > MAX_WM_SIZE:
                bot.delete_message(m.chat.id, msg.message_id)
                reply_temp(m, "⚠️ File is too large! (Max 20MB)")
                return

            # 4. Download File
            downloaded = bot.download_file(file_info.file_path)
            
            # Determine Extension
            ext = ".mp4" if file_type == 'video' else (".gif" if file_type == 'gif' else ".jpg")
            
            # Unique Filenames
            in_path = f"temp_grp_in_{m.chat.id}_{m.message_id}{ext}"
            out_path = f"temp_grp_out_{m.chat.id}_{m.message_id}{ext}"
            
            with open(in_path, 'wb') as f: f.write(downloaded)

            # 5. Load Settings (From Global WM Data)
            settings = get_wm_settings(m.chat.id).copy()
            
            # Custom Text Override (/wm MyText)
            parts = m.text.split(maxsplit=1)
            if len(parts) > 1:
                settings['text'] = parts[1]

            # 6. Call Engine
            success = False
            if file_type == 'photo':
                success = apply_watermark_image(in_path, out_path, settings)
            else:
                bot.edit_message_text(f"🎬 Rendering {file_type.title()}... This may take a moment.", m.chat.id, msg.message_id)
                success = apply_watermark_video(in_path, out_path, settings, is_gif=(file_type=='gif'))

            # 7. Send Result
            if success:
                with open(out_path, 'rb') as f:
                    if file_type == 'photo':
                        bot.send_photo(m.chat.id, f, reply_to_message_id=reply.message_id)
                    elif file_type == 'video':
                        bot.send_video(m.chat.id, f, reply_to_message_id=reply.message_id)
                    elif file_type == 'gif':
                        bot.send_animation(m.chat.id, f, reply_to_message_id=reply.message_id)
                
                # Delete Loading Message on Success
                bot.delete_message(m.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Processing Failed.", m.chat.id, msg.message_id)

            # 8. Cleanup
            if os.path.exists(in_path): os.remove(in_path)
            if os.path.exists(out_path): os.remove(out_path)

        except Exception as e:
            bot.edit_message_text(f"❌ Error: {e}", m.chat.id, msg.message_id)
            if os.path.exists(in_path): os.remove(in_path)

    # --- B. URL SHORTENER (/short) ---
    @bot.message_handler(commands=['short', 'url'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def handle_short_command(message):
        if not URL_SHORTENER_AVAILABLE:
            reply_temp(message, "⚠️ URL Shortener tool is currently unavailable.")
            return
        
        # Check if URL Shortener is enabled in Group Settings
        group_data = get_data(message.chat.id)
        if not group_data['tools']['url_shortener']: return

        # Check for Link
        target_text = None
        
        if len(message.text.split()) > 1:
            # Case 1: Command with Link (/short google.com)
            target_text = message.text.split(maxsplit=1)[1]
        elif message.reply_to_message and message.reply_to_message.text:
            # Case 2: Reply to a Link
            target_text = message.reply_to_message.text
        
        if target_text:
            # Modify message object to pass just the URL to the processor
            message.text = target_text
            process_url(bot, message)
        else:
            reply_temp(message, "⚠️ **Usage:**\n`/short <link>`\nOr reply to a link with `/short`")

    # --- C. DOWNLOADER (Placeholder) ---
    @bot.message_handler(commands=['dl', 'download'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_tool_dl(m):
        data = get_data(m.chat.id)
        if not data['tools']['downloader']: return
        
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            reply_temp(m, "🔗 Link required. Example: `/dl <link>`")
            return
        
        bot.reply_to(m, f"🔍 Processing... {parts[1]}") 

    # --- D. WEATHER (Placeholder) ---
    @bot.message_handler(commands=['weather'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_tool_weather(m):
        data = get_data(m.chat.id)
        if not data['tools']['weather']: return

        parts = m.text.split(maxsplit=1)
        if len(parts) < 2:
            reply_temp(m, "🌤 City name required. Example: `/weather Dhaka`")
            return
            
        bot.reply_to(m, f"🌤 Checking weather for {parts[1]}...") 

    # ---------------------------------------------
    # 2. ADMIN MANAGEMENT COMMANDS (Ghost Mode 👻)
    # ---------------------------------------------
    
    # Helper for Text Updates
    def update_text_safely(message, key):
        if not is_admin(bot, message.chat.id, message.from_user.id): return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            reply_temp(message, f"⚠️ Usage: `/set{key} <text>`")
            return
        get_data(message.chat.id)['texts'][key] = parts[1].strip()
        reply_temp(message, f"✅ **{key.upper()}** message updated!")

    @bot.message_handler(commands=['rules'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_rules(m):
        # Rules are public, do not auto-delete
        rules = get_data(m.chat.id)['texts'].get('rules', "No rules set.")
        bot.reply_to(m, rules, parse_mode="Markdown")

    @bot.message_handler(commands=['ban', 'mute', 'unmute', 'kick', 'warn'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_actions(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        if not m.reply_to_message:
            reply_temp(m, "⚠️ Reply to a user to perform action.")
            return
        
        target = m.reply_to_message.from_user
        if is_admin(bot, m.chat.id, target.id):
            reply_temp(m, "⚠️ Cannot act on Admins.")
            return

        cmd = m.text.split()[0][1:]
        try:
            if cmd == 'warn': 
                handle_warning(bot, m, target)
            else: 
                perform_action(bot, m.chat.id, target, cmd, m)
                
            # Clean up command on success
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass
            
        except Exception as e:
            reply_temp(m, f"❌ Error: {e}")

    # Pin/Unpin
    @bot.message_handler(commands=['pin'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_pin(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        if not m.reply_to_message: return
        try:
            bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
            reply_temp(m, "📌 Pinned.")
        except: reply_temp(m, "❌ Failed.")

    @bot.message_handler(commands=['unpin'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_unpin(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        try:
            if m.reply_to_message: bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
            else: bot.unpin_chat_message(m.chat.id)
            reply_temp(m, "📌 Unpinned.")
        except: pass

    @bot.message_handler(commands=['unwarn'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_unwarn(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        if not m.reply_to_message: return
        data = get_data(m.chat.id)
        if m.reply_to_message.from_user.id in data['warns']:
            del data['warns'][m.reply_to_message.from_user.id]
            reply_temp(m, "✅ Warning reset.")
        else: reply_temp(m, "⚠️ No warnings found.")

    # Text Settings
    @bot.message_handler(commands=['setwelcome'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def s_wel(m): update_text_safely(m, 'welcome')

    @bot.message_handler(commands=['setrules'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def s_rul(m): update_text_safely(m, 'rules')

    @bot.message_handler(commands=['setban'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def s_ban(m): update_text_safely(m, 'ban')

    @bot.message_handler(commands=['setmute'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def s_mute(m): update_text_safely(m, 'mute')
    
    @bot.message_handler(commands=['setunmute'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def s_unmute(m): update_text_safely(m, 'unmute')

    @bot.message_handler(commands=['setwarn'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def s_warn(m): update_text_safely(m, 'warn')

    # Ban Words
    @bot.message_handler(commands=['addword'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_addword(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2: 
            reply_temp(m, "⚠️ Usage: `/addword xyz`")
            return
        word = parts[1].strip().lower()
        data = get_data(m.chat.id)
        if word not in data['banwords']:
            data['banwords'].append(word)
            reply_temp(m, f"✅ '{word}' added to banlist.")
        else:
             reply_temp(m, "⚠️ Word already exists.")

    @bot.message_handler(commands=['delword'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_delword(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        parts = m.text.split(maxsplit=1)
        if len(parts) < 2: 
            reply_temp(m, "⚠️ Usage: `/delword xyz`")
            return
        word = parts[1].strip().lower()
        data = get_data(m.chat.id)
        if word in data['banwords']:
            data['banwords'].remove(word)
            reply_temp(m, f"✅ '{word}' removed.")
        else:
            reply_temp(m, "⚠️ Word not found.")

    @bot.message_handler(commands=['banlist'], func=lambda m: m.chat.type in ['group', 'supergroup'])
    def cmd_banlist(m):
        if not is_admin(bot, m.chat.id, m.from_user.id): return
        data = get_data(m.chat.id)
        if not data['banwords']: 
            reply_temp(m, "📂 Banlist is empty.")
        else: 
            # Show list for 10 seconds
            reply_temp(m, f"🚫 **Banned Words:**\n" + ", ".join([f"`{w}`" for w in data['banwords']]), delay=10)
