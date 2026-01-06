import telebot
from config import BOT_TOKEN
from handlers.start import register_start
from handlers.auth import register_auth_handlers
from handlers.admin_panel import register_admin_handlers
from handlers.broadcast import register_broadcast_handlers
from handlers.shop_seller import register_seller_handlers
from handlers.shop_buyer import register_buyer_handlers # <--- Add this
from handlers.callbacks import register_callbacks

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Register Handlers
register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)
register_broadcast_handlers(bot)
register_seller_handlers(bot)
register_buyer_handlers(bot) # <--- Register this
register_callbacks(bot)

print("🤖 Bot is running...")
bot.infinity_polling()
