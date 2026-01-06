# handlers/callbacks.py
from utils import is_admin
from keyboards.main_menu import get_tools_layout, main_menu

# NOTE: Do NOT import handlers.admin_panel here at the top!
# It causes the crash.

def register_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        # ✅ FIX: Import INSIDE the function. 
        # This prevents the circular error.
        from handlers.admin_panel import send_admin_panel
        
        data = call.data
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        if data == "tools":
            text, kb = get_tools_layout()
            bot.send_message(chat_id, text, reply_markup=kb)
            
        elif data == "main_menu_return":
            bot.delete_message(chat_id, message_id)
            bot.send_message(
                chat_id, 
                "👋 <b>Welcome Back</b>", 
                reply_markup=main_menu(user_id) 
            )

        elif data == "admin":
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "⛔ Access Denied", show_alert=True)
                return
            # Now we use the imported function safely
            send_admin_panel(bot, chat_id)

        elif data == "shop":
            bot.send_message(chat_id, "🛒 Shop coming soon")
        elif data == "manager":
            bot.send_message(chat_id, "📢 Manager coming soon")
            
        elif data.startswith("tool_"):
            bot.answer_callback_query(call.id, f"Selected: {data}")
