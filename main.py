import telebot
from config import BOT_TOKEN
from handlers.start import register_start
from handlers.callbacks import register_callbacks

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

register_start(bot)
register_callbacks(bot)

print("🤖 Bot is running successfully...")
bot.infinity_polling()
