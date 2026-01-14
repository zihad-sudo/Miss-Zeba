from keyboards.main_menu import main_menu, tools_layout, tool_url_shorten_menu
from utils.utils import is_admin
from handlers.tools import url_shorten

def register_callbacks(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        data = call.data

        # ------------------------------
        # Tools menu
        # ------------------------------
        if data == "tools":
            text, kb = tools_layout()
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
            except:
                pass

        # ------------------------------
        # URL Shortener menu
        # ------------------------------
        elif data == "tool_url_shortener":
            state = url_shorten.user_state.get(chat_id, {"emoji": True, "qr": True})
            text, kb = tool_url_shorten_menu(chat_id, state)
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
            except:
                pass

        # ------------------------------
        # Toggle Emoji mode
        # ------------------------------
        elif data == "toggle_emoji":
            state = url_shorten.user_state.get(chat_id, {"emoji": True, "qr": True})
            state["emoji"] = not state["emoji"]
            url_shorten.user_state[chat_id] = state
            text, kb = tool_url_shorten_menu(chat_id, state)
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
            except:
                pass

        # ------------------------------
        # Toggle QR mode
        # ------------------------------
        elif data == "toggle_qr":
            state = url_shorten.user_state.get(chat_id, {"emoji": True, "qr": True})
            state["qr"] = not state["qr"]
            url_shorten.user_state[chat_id] = state
            text, kb = tool_url_shorten_menu(chat_id, state)
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=kb)
            except:
                pass

        # ------------------------------
        # Back to Main Menu
        # ------------------------------
        elif data == "main_menu_return":
            kb = main_menu(chat_id)
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Welcome!", reply_markup=kb)
            except:
                pass


    # ------------------------------
    # Handle direct URL messages
    # ------------------------------
    @bot.message_handler(func=lambda message: True)
    def handle_direct_url(message):
        chat_id = message.chat.id
        # If user clicked URL Shortener before, process directly
        if chat_id in url_shorten.user_state:
            url_shorten.process_url(bot, message)
