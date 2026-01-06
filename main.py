import telebot
from config import BOT_TOKEN
from handlers.start import register_start
from handlers.callbacks import register_callbacks
from handlers.admin_panel import register_admin_handlers # <--- Import this

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

register_start(bot)
register_admin_handlers(bot) # <--- Register BEFORE callbacks to ensure priority
register_callbacks(bot)

print("🤖 Bot is running...")
bot.infinity_polling()
