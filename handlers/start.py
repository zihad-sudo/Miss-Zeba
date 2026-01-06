from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import main_menu
from utils import get_text, track_user
from utils_shop import get_shop # <--- Import this

def register_start(bot):
    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id
        track_user(message.from_user)
        
        args = message.text.split()
        
        # --- SCENARIO 1: VISITING A SHOP ---
        # Checks if link looks like: /start shop_123456
        if len(args) > 1 and args[1].startswith("shop_"):
            shop_owner_id = args[1].replace("shop_", "")
            shop = get_shop(shop_owner_id)
            
            if shop:
                # Show the Shop Front (Buyer View)
                text = (
                    f"🏪 <b>Welcome to {shop['name']}</b>\n"
                    f"<i>{shop['description']}</i>\n\n"
                    f"👇 <b>Browse our products below:</b>"
                )
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("📦 Browse Products", callback_data=f"view_prods_{shop_owner_id}"))
                kb.add(InlineKeyboardButton("🏠 Create My Own Shop", callback_data="main_menu_return"))
                
                bot.send_message(message.chat.id, text, reply_markup=kb)
                return
            else:
                bot.send_message(message.chat.id, "❌ <b>Error:</b> This shop does not exist or was deleted.")
                # Fall through to normal welcome
        
        # --- SCENARIO 2: NORMAL WELCOME ---
        welcome_text = get_text("start_message", "👋 Welcome!")
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=main_menu(user_id)
        )
