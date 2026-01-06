# handlers/start.py
from keyboards.main_menu import main_menu
from utils import get_text

def register_start(bot):
    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id
        welcome_text = get_text("start_message", "👋 Welcome!")
        
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=main_menu(user_id)
        )
