import telebot
import time
import threading
from config import BOT_TOKEN
from handlers.start import register_start
from handlers.auth import register_auth_handlers
from handlers.admin_panel import register_admin_handlers
from handlers.broadcast import register_broadcast_handlers
from handlers.shop_seller import register_seller_handlers
from handlers.shop_buyer import register_buyer_handlers
from handlers.shop_categories import register_category_handlers
from handlers.shop_requests import register_request_handlers 
from handlers.shop_social import register_social_handlers, post_product_to_channel
from handlers.shop_coupons import register_coupon_handlers
from handlers.shop_orders import register_order_handlers
from handlers.shop_analytics import register_analytics_handlers
from handlers.shop_cart import register_cart_handlers # <--- Added
from handlers.callbacks import register_callbacks
from utils_shop import get_and_clear_due_posts

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
register_coupon_handlers(bot)
register_order_handlers(bot)
register_analytics_handlers(bot)
register_cart_handlers(bot) # <--- Register
register_callbacks(bot)

def scheduler_loop():
    print("⏰ Scheduler started...")
    while True:
        try:
            tasks = get_and_clear_due_posts()
            if tasks:
                for t in tasks:
                    post_product_to_channel(bot, t['channel_id'], t['product'], t['shop_name'], None, bot.get_me().username)
            time.sleep(60) 
        except Exception as e:
            print(f"Scheduler Error: {e}")
            time.sleep(60)

threading.Thread(target=scheduler_loop, daemon=True).start()

print("🤖 Bot is running...")
bot.infinity_polling()
