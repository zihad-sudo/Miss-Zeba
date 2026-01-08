import telebot
from config import BOT_TOKEN
from handlers.start import register_start
from handlers.auth import register_auth_handlers
from handlers.admin_panel import register_admin_handlers
from handlers.broadcast import register_broadcast_handlers
from handlers.shop_seller import register_seller_handlers
from handlers.shop_buyer import register_buyer_handlers
from handlers.shop_categories import register_category_handlers
from handlers.shop_requests import register_request_handlers 
from handlers.shop_social import register_social_handlers
from handlers.callbacks import register_callbacks

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)
register_broadcast_handlers(bot)
register_seller_handlers(bot)
register_buyer_handlers(bot)
register_category_handlers(bot)
register_request_handlers(bot)
register_social_handlers(bot)
register_callbacks(bot)

print("🤖 Bot is running...")
bot.infinity_polling()
