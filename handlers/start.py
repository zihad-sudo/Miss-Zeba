#handelers/start.py
from keyboards.main_menu import main_menu
from utils import get_text

def register_start(bot):
    @bot.message_handler(commands=["start"])
    def start(message):
        bot.send_message(
            message.chat.id,
            get_text("start_message", "<b>Welcome Dummy Dummy</b>\n\n<i>Ajaira Khaia Kam naiga!</i>"),
            reply_markup=main_menu()
        )
