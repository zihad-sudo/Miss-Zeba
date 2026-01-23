import telebot
from telebot import types
import traceback

# =========================================================
# 👇 TOOL REGISTRY & IMPORTS
# =========================================================
tool_registry = {}

# URL Tool Import
try:
    from handlers.tools.url_shorten.core import open_url_tool
    tool_registry['tool_url_shortener'] = lambda bot, msg: open_url_tool(bot, msg, is_edit=True)
except ImportError: pass

# Watermark Tool Import
try:
    def wm_tool_gateway(bot, msg):
        from handlers.tools.watermark.core import refresh_main_menu, user_states_watermark
        user_states_watermark[msg.chat.id] = "waiting_media"
        refresh_main_menu(bot, msg.chat.id)
    tool_registry['tool_img'] = wm_tool_gateway
except ImportError: pass

# Menu Import
try:
    from keyboards.main_menu import main_menu, tools_layout
except ImportError:
    def main_menu(uid): return None
    def tools_layout(): return "⚠️ Menu Error", None

# =========================================================
# 🎮 CALLBACK HANDLER (FIXED FOR MEDIA MESSAGES)
# =========================================================
def register_callbacks(bot):

    # Catch-all handler
    @bot.callback_query_handler(func=lambda call: not (call.data.startswith("wm_") or call.data.startswith("url_")))
    def handle_global_callbacks(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        data = call.data

        try:
            # 1. Tool Openers
            if data in tool_registry:
                bot.answer_callback_query(call.id)
                tool_registry[data](bot, call.message)
                return

            # -------------------------------------------------
            # 🛠 2. TOOLS MENU NAVIGATION (FIXED HERE) 🚨
            # -------------------------------------------------
            if data in ["tools", "back_to_tools"]:
                bot.answer_callback_query(call.id)
                text, kb = tools_layout()
                
                if kb:
                    # ✅ ফিক্স: যদি আগের মেসেজটি ছবি (QR Code) হয়, তবে এডিট করা যাবে না। 
                    # তাই ডিলিট করে নতুন মেসেজ পাঠানো হচ্ছে।
                    if call.message.content_type == 'text':
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=text,
                            reply_markup=kb,
                            parse_mode="Markdown"
                        )
                    else:
                        # মিডিয়া মেসেজ হলে ডিলিট করে সেন্ড
                        bot.delete_message(chat_id, message_id)
                        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")
                else:
                    bot.answer_callback_query(call.id, "⚠️ Menu Error", show_alert=True)
                return

            # -------------------------------------------------
            # 🏠 3. MAIN MENU RETURN (FIXED HERE TOO) 🚨
            # -------------------------------------------------
            if data == "main_menu_return":
                bot.answer_callback_query(call.id)
                kb = main_menu(call.from_user.id)
                
                if kb:
                    # এখানেও একই ফিক্স প্রয়োগ করা হলো
                    if call.message.content_type == 'text':
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text="🏠 **Main Menu**\n\nChoose an option below:",
                            reply_markup=kb,
                            parse_mode="Markdown"
                        )
                    else:
                        bot.delete_message(chat_id, message_id)
                        bot.send_message(chat_id, "🏠 **Main Menu**\n\nChoose an option below:", reply_markup=kb, parse_mode="Markdown")
                else:
                    # মেনু লোড না হলে রিস্টার্ট
                    bot.delete_message(chat_id, message_id)
                    from handlers.start import send_welcome
                    send_welcome(bot, call.message)
                return

            # 4. Info Popups
            if data == "open_management":
                bot.answer_callback_query(call.id, "ℹ️ Use /help in group.", show_alert=True)
                return
            
            if data == "tool_weather":
                bot.answer_callback_query(call.id, "ℹ️ Use /weather <city>", show_alert=True)
                return

            # 5. Close
            if data == "close":
                bot.delete_message(chat_id, message_id)
                return

            # 6. Unknown
            bot.answer_callback_query(call.id, "⚠️ Unknown action.")

        except Exception as e:
            print(f"Callback Error: {e}")
            traceback.print_exc() # বিস্তারিত এরর লগ দেখার জন্য
            try: bot.answer_callback_query(call.id, "❌ Error")
            except: pass
