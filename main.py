# main.py
import telebot
from config import BOT_TOKEN
from handlers.start import register_start
from handlers.auth import register_auth_handlers
from handlers.admin_panel import register_admin_handlers
from handlers.callbacks import register_callbacks

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in config.py")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Register Handlers in this specific order
register_start(bot)
register_auth_handlers(bot)
register_admin_handlers(bot)
register_callbacks(bot)

print("🤖 Bot is running...")
bot.infinity_polling()
