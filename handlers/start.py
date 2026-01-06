from keyboards.main_menu import main_menu

def register_start(bot):
    @bot.message_handler(commands=["start"])
    def start(message):
        bot.send_message(
            message.chat.id,
            "👋 <b>Welcome to All-in-One Telegram Bot</b>\n\nSystem deployed successfully.",
            reply_markup=main_menu()
        )
