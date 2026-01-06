from config import SUPER_ADMINS

def register_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        data = call.data
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if data == "tools":
            bot.send_message(chat_id, "🛠 Tools coming soon")
        elif data == "shop":
            bot.send_message(chat_id, "🛒 Shop coming soon")
        elif data == "manager":
            bot.send_message(chat_id, "📢 Manager coming soon")
        elif data == "admin":
            if user_id not in SUPER_ADMINS:
                bot.answer_callback_query(call.id, "Admin only", show_alert=True)
                return
            bot.send_message(chat_id, "👮 Admin panel coming soon")
