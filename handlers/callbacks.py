import telebot
from telebot import types
import traceback  # এরর ট্রেস করার জন্য

# =========================================================
# 👇 IMPORT AREA (Safe Imports)
# =========================================================

# 1. URL Shortener Tool (From core.py)
try:
    from handlers.tools.url_shorten.core import open_url_tool
    URL_TOOL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Callback Import Error (URL Tool): {e}")
    URL_TOOL_AVAILABLE = False
    open_url_tool = None

# 2. Main Menu & Tools Layout (From keyboard folder)
try:
    # আপনার ফোল্ডারের নাম 'keyboards' নিশ্চিত করুন (keyboards নয়)
    from keyboards.main_menu import main_menu, tools_layout
except ImportError as e:
    print(f"❌ Callback Import Error (Menus): {e}")
    # বিস্তারিত এরর দেখার জন্য
    traceback.print_exc()
    
    # ফলব্যাক ফাংশন (যাতে বট ক্র্যাশ না করে)
    def main_menu(uid): return None
    def tools_layout(): return "⚠️ Menu Error: Check Console", None

# 3. Watermark Tool (Optional)
try:
    from handlers.tools.watermark.engine import apply_watermark_image
    WATERMARK_AVAILABLE = True
except ImportError:
    WATERMARK_AVAILABLE = False

# =========================================================
# 🎮 CALLBACK HANDLER REGISTRATION
# =========================================================
def register_callbacks(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_global_callbacks(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        data = call.data

        try:
            # ------------------------------
            # 🔗 1. URL SHORTENER (Edit Mode)
            # ------------------------------
            if data == "tool_url_shortener":
                if URL_TOOL_AVAILABLE and open_url_tool:
                    # 🔥 Message Edit করে টুল ওপেন করবে
                    open_url_tool(bot, call.message, is_edit=True)
                else:
                    bot.answer_callback_query(call.id, "⚠️ Tool is currently unavailable.", show_alert=True)

            # ------------------------------
            # 🛠 2. TOOLS MENU (Navigation)
            # ------------------------------
            # 'tools' = মেইন মেনু থেকে আসা
            # 'back_to_tools' = URL টুল বা অন্য টুল থেকে ব্যাকে আসা
            elif data in ["tools", "back_to_tools"]:
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

            # ------------------------------
            # 🏠 3. BACK TO MAIN MENU
            # ------------------------------
            elif data == "main_menu_return":
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
                    # যদি এডিট ফেইল করে (মেসেজ টাইপ মিসম্যাচ), নতুন করে পাঠাবে
                    bot.delete_message(chat_id, message_id)
                    from handlers.start import send_welcome
                    send_welcome(bot, call.message)

            # ------------------------------
            # 🎨 4. WATERMARK TOOL
            # ------------------------------
            elif data == "tool_img":
                text = (
                    "🎨 **Watermark Studio**\n\n"
                    "To use this tool:\n"
                    "1. Send a **Photo** or **Video** to the bot.\n"
                    "2. Reply to it with `/wm` command.\n\n"
                    "You can setup your watermark in Admin Panel."
                )
                # এটি শুধু ইনফো শো করবে, মেনু এডিট করবে না (Back বাটন রাখার জন্য আলাদা লজিক লাগতে পারে)
                # অথবা আমরা এখানে একটি ব্যাক বাটন সহ মেসেজ এডিট করতে পারি:
                back_kb = types.InlineKeyboardMarkup()
                back_kb.add(types.InlineKeyboardButton("🔙 Back to Tools", callback_data="back_to_tools"))
                
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=back_kb,
                    parse_mode="Markdown"
                )

            # ------------------------------
            # 🛡️ 5. GROUP MANAGEMENT
            # ------------------------------
            elif data == "open_management":
                bot.answer_callback_query(call.id, "ℹ️ Use /help in your group to see commands.", show_alert=True)

            # ------------------------------
            # 🌤 6. WEATHER
            # ------------------------------
            elif data == "tool_weather":
                bot.answer_callback_query(call.id, "ℹ️ Use /weather <city> command.", show_alert=True)

            # ------------------------------
            # ❌ 7. CLOSE ACTION
            # ------------------------------
            elif data == "close":
                bot.delete_message(chat_id, message_id)

            # ------------------------------
            # ❓ UNKNOWN CALLBACKS
            # ------------------------------
            else:
                # অন্য কোনো হ্যান্ডলার থাকলে (যেমন Shop) সেগুলো এখানে হ্যান্ডল হবে
                pass

        except Exception as e:
            print(f"⚠️ Callback Logic Error: {e}")
            # traceback.print_exc() # ডিবাগিংয়ের জন্য এটি আনকমেন্ট করতে পারেন
            try:
                bot.answer_callback_query(call.id, "❌ Error processing request.")
            except: pass
