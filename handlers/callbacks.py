# handlers/callbacks.py

import telebot
from telebot import types
import traceback

# =========================================================
# 👇 TOOL IMPORTS & REGISTRY
# =========================================================
tool_registry = {}

# --- 1. URL Shortener ---
try:
    from handlers.tools.url_shorten.core import open_url_tool
    # এটি টুলটি ওপেন করার প্রাথমিক গেটওয়ে
    tool_registry['tool_url_shortener'] = lambda bot, msg: open_url_tool(bot, msg, is_edit=True)
except ImportError as e:
    print(f"⚠️ Callback Import Error (URL Tool): {e}")

# --- 2. Watermark Tool ---
try:
    # Watermark টুল ওপেন করার প্রাথমিক গেটওয়ে
    def wm_tool_gateway(bot, msg):
        from handlers.tools.watermark.core import refresh_main_menu, user_states_watermark
        user_states_watermark[msg.chat.id] = "waiting_media"
        refresh_main_menu(bot, msg.chat.id)
        
    tool_registry['tool_img'] = wm_tool_gateway
except ImportError as e:
    print(f"⚠️ Callback Import Error (Watermark Tool): {e}")

# --- 3. Main Menu & Tools Layout ---
try:
    from keyboards.main_menu import main_menu, tools_layout
except ImportError as e:
    print(f"❌ Callback Import Error (Menus): {e}")
    def main_menu(uid): return None
    def tools_layout(): return "⚠️ Menu Error: Check Console", None

# =========================================================
# 🎮 CALLBACK HANDLER REGISTRATION
# =========================================================
def register_callbacks(bot):

    # 🔥 CRITICAL FIX: এটি শুধু জেনারেল কলব্যাকগুলো ধরবে। 
    # url_ বা wm_ দিয়ে শুরু হওয়া কলব্যাকগুলো তাদের নিজ নিজ core.py হ্যান্ডেল করবে।
    @bot.callback_query_handler(func=lambda call: not (call.data.startswith("wm_") or call.data.startswith("url_")))
    def handle_global_callbacks(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        data = call.data

        try:
            # ------------------------------
            # 🚀 TOOL OPENER (Initial Click)
            # ------------------------------
            if data in tool_registry:
                bot.answer_callback_query(call.id)
                tool_registry[data](bot, call.message)
                return

            # ------------------------------
            # 🛠 TOOLS MENU NAVIGATION
            # ------------------------------
            if data in ["tools", "back_to_tools"]:
                bot.answer_callback_query(call.id)
                text, kb = tools_layout()
                if kb:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
                else:
                    bot.answer_callback_query(call.id, "⚠️ Menu failed to load!", show_alert=True)
                return

            # ------------------------------
            # 🏠 MAIN MENU
            # ------------------------------
            if data == "main_menu_return":
                bot.answer_callback_query(call.id)
                kb = main_menu(call.from_user.id)
                if kb:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text="🏠 **Main Menu**\n\nChoose an option below:",
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
                else:
                    # যদি মেনু না পাওয়া যায় তবে স্টার্ট মেসেজ পাঠানো
                    bot.delete_message(chat_id, message_id)
                    from handlers.start import send_welcome
                    send_welcome(bot, call.message)
                return

            # ------------------------------
            # 🛡️ GROUP MANAGEMENT
            # ------------------------------
            if data == "open_management":
                bot.answer_callback_query(call.id, "ℹ️ Use /help in your group to see commands.", show_alert=True)
                return

            # ------------------------------
            # 🌤 WEATHER
            # ------------------------------
            if data == "tool_weather":
                bot.answer_callback_query(call.id, "ℹ️ Use /weather <city> command.", show_alert=True)
                return

            # ------------------------------
            # ❌ CLOSE
            # ------------------------------
            if data == "close":
                bot.answer_callback_query(call.id)
                bot.delete_message(chat_id, message_id)
                return

            # ------------------------------
            # ❓ UNKNOWN CALLBACK
            # ------------------------------
            # এখানে এসে থামবে যদি উপরের কোনোটিই ম্যাচ না করে
            bot.answer_callback_query(call.id, "⚠️ Unknown action.")

        except Exception as e:
            print(f"⚠️ Global Callback Error: {e}")
            traceback.print_exc()
            try:
                bot.answer_callback_query(call.id, "❌ Error processing request.")
            except: pass
