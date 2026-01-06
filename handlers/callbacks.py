from config import SUPER_ADMINS
from keyboards.main_menu import get_tools_layout, main_menu
# Import the new function
from handlers.admin_panel import send_admin_panel 

def register_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        data = call.data
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        # --- ADMIN BUTTON LOGIC ---
        if data == "admin":
            if user_id not in SUPER_ADMINS:
                bot.answer_callback_query(call.id, "⛔ Admins Only", show_alert=True)
                return
            
            # Launch the visual panel
            send_admin_panel(bot, chat_id)

        # --- EXISTING LOGIC ---
        elif data == "tools":
            text, kb = get_tools_layout()
            bot.send_message(chat_id, text, reply_markup=kb)

        elif data == "shop":
            bot.send_message(chat_id, "🛒 Shop coming soon")

        elif data == "manager":
            bot.send_message(chat_id, "📢 Manager coming soon")

        elif data == "main_menu_return":
            bot.delete_message(chat_id, message_id)
            # Example of dynamic start message if you want it:
            # from utils import get_text
            # welcome_text = get_text("start_message", "Welcome!")
            bot.send_message(chat_id, "👋 Welcome Back", reply_markup=main_menu())
            
        elif data.startswith("tool_"):
            bot.answer_callback_query(call.id, f"Clicked: {data}")
