import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils_shop import get_shop, add_product_review, get_product_reviews

review_sessions = {}

def register_social_handlers(bot):

    @bot.callback_query_handler(func=lambda c: c.data == "shop_broadcast")
    def start_broadcast(call):
        msg = bot.send_message(call.message.chat.id, "📢 <b>Broadcast</b>\nSend the message to broadcast.")
        bot.register_next_step_handler(msg, process_broadcast, bot)

    def process_broadcast(message, bot):
        shop = get_shop(message.from_user.id)
        if not shop: return
        buyers = shop.get("approved_users", [])
        if not buyers:
            bot.send_message(message.chat.id, "❌ No approved buyers.")
            return
        bot.send_message(message.chat.id, f"⏳ Sending to {len(buyers)} users...")
        count = 0
        blocked = 0
        for uid in buyers:
            try:
                if message.content_type == 'text':
                    bot.send_message(uid, f"📢 <b>From {shop['name']}</b>\n\n{message.text}", parse_mode="HTML")
                elif message.content_type == 'photo':
                    bot.send_photo(uid, message.photo[-1].file_id, caption=f"📢 <b>From {shop['name']}</b>\n\n{message.caption or ''}", parse_mode="HTML")
                count += 1
            except: blocked += 1
        bot.send_message(message.chat.id, f"✅ Sent: {count}\n❌ Failed: {blocked}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rate_prod_"))
    def start_rating(call):
        parts = call.data.split("_")
        shop_id, prod_id = parts[2], "_".join(parts[3:])
        kb = InlineKeyboardMarkup(row_width=5)
        btns = [InlineKeyboardButton(f"{i}⭐", callback_data=f"set_star_{shop_id}_{prod_id}_{i}") for i in range(1, 6)]
        kb.add(*btns)
        kb.add(InlineKeyboardButton("❌ Cancel", callback_data=f"sh_view_{shop_id}_{prod_id}"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✍️ <b>Rate Product:</b>", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_star_"))
    def set_star_rating(call):
        parts = call.data.split("_")
        shop_id, prod_id, rating = parts[2], parts[3], int(parts[4])
        review_sessions[call.from_user.id] = {'shop_id': shop_id, 'prod_id': prod_id, 'rating': rating}
        msg = bot.send_message(call.message.chat.id, f"⭐ <b>{rating} Stars!</b>\nSend a short review text:")
        bot.register_next_step_handler(msg, process_review_text, bot)

    def process_review_text(message, bot):
        user_id = message.from_user.id
        data = review_sessions.get(user_id)
        if not data: return
        add_product_review(data['shop_id'], data['prod_id'], user_id, message.from_user.first_name, data['rating'], message.text)
        bot.send_message(message.chat.id, "✅ Review Posted!")
        del review_sessions[user_id]
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Back to Product", callback_data=f"sh_view_{data['shop_id']}_{data['prod_id']}"))
        bot.send_message(message.chat.id, "Thanks!", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("view_revs_"))
    def view_reviews(call):
        parts = call.data.split("_")
        shop_id, prod_id = parts[2], "_".join(parts[3:])
        reviews = get_product_reviews(shop_id, prod_id)
        if not reviews:
            bot.answer_callback_query(call.id, "No reviews yet.", show_alert=True)
            return
        text = f"⭐ <b>Reviews</b>\n\n"
        for r in reviews[-5:]: text += f"👤 <b>{r['name']}</b> ({r['rating']}⭐)\n💬 <i>{r['text']}</i>\n\n"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Back", callback_data=f"sh_view_{shop_id}_{prod_id}"))
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
