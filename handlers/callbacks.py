from config import SUPER_ADMINS
from keyboards.main_menu import get_tools_layout, main_menu

def register_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        data = call.data
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        if data == "tools":
            # Get dynamic content
            text, kb = get_tools_layout()
            # Send as new message
            bot.send_message(chat_id, text, reply_markup=kb)

        elif data == "main_menu_return":
            # Go back to main menu (Editing the message looks smoother here)
            bot.edit_message_text(
                chat_id=chat_id, 
                message_id=message_id,
                text="👋 <b>Welcome to All-in-One Telegram Bot</b>",
                reply_markup=main_menu()
            )

        elif data == "shop":
            bot.send_message(chat_id, "🛒 Shop coming soon")
        elif data == "manager":
            bot.send_message(chat_id, "📢 Manager coming soon")
        elif data == "admin":
            if user_id not in SUPER_ADMINS:
                bot.answer_callback_query(call.id, "Admin only", show_alert=True)
                return
            bot.send_message(chat_id, "👮 Admin panel coming soon")
