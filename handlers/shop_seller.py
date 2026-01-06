import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils_shop import get_shop, create_shop, add_product_to_shop, update_shop_desc

def register_seller_handlers(bot):
    
    # --- ENTRY POINT: My Business ---
    @bot.callback_query_handler(func=lambda c: c.data == "my_business")
    def open_business_menu(call):
        user_id = call.from_user.id
        shop = get_shop(user_id)
        
        if not shop:
            msg = bot.send_message(
                call.message.chat.id,
                "💼 <b>Start Your Business</b>\n\n"
                "You don't have a shop yet.\n"
                "👇 <b>Enter your Shop Name to create one:</b>"
            )
            bot.register_next_step_handler(msg, process_create_shop, bot)
        else:
            show_dashboard(bot, call.message, shop)

    # --- DASHBOARD VIEW ---
    def show_dashboard(bot, message, shop):
        user_id = shop['owner_id']
        shop_link = f"https://t.me/{bot.get_me().username}?start=shop_{user_id}"
        
        text = (
            f"🏪 <b>{shop['name']}</b>\n\n"
            f"🔗 <b>Link:</b> <code>{shop_link}</code>\n\n"
            f"📦 <b>Products:</b> {len(shop['products'])}\n"
            f"📝 <b>Desc:</b> {shop['description']}"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➕ Add Product", callback_data="shop_add_prod"))
        kb.add(InlineKeyboardButton("✏️ Edit Description", callback_data="shop_edit_info"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="main_menu_return"))
        
        # We use try/except in case we are trying to edit a message exactly same as before
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=text,
                reply_markup=kb,
                disable_web_page_preview=True
            )
        except:
            bot.send_message(message.chat.id, text, reply_markup=kb)

    # ==========================
    # ➕ ADD PRODUCT FLOW
    # ==========================
    
    @bot.callback_query_handler(func=lambda c: c.data == "shop_add_prod")
    def start_add_product(call):
        msg = bot.send_message(
            call.message.chat.id,
            "📸 <b>Step 1/3: Send Product Photo</b>\n"
            "Please send an image for your product."
        )
        bot.register_next_step_handler(msg, process_prod_photo, bot)

    def process_prod_photo(message, bot):
        if not message.photo:
            bot.send_message(message.chat.id, "❌ Please send a PHOTO.")
            return

        # Get the largest version of the photo
        photo_id = message.photo[-1].file_id
        
        msg = bot.send_message(message.chat.id, "📝 <b>Step 2/3: Enter Product Name</b>\n(e.g., Netflix 4K)")
        bot.register_next_step_handler(msg, process_prod_name, bot, photo_id)

    def process_prod_name(message, bot, photo_id):
        name = message.text
        msg = bot.send_message(message.chat.id, "💰 <b>Step 3/3: Enter Price</b>\n(e.g., 350 BDT)")
        bot.register_next_step_handler(msg, process_prod_price, bot, photo_id, name)

    def process_prod_price(message, bot, photo_id, name):
        price = message.text
        user_id = message.from_user.id
        
        if add_product_to_shop(user_id, name, price, photo_id):
            bot.send_message(message.chat.id, f"✅ <b>Product Added!</b>\n\n📦 {name} - {price}")
            # Refresh Dashboard
            shop = get_shop(user_id)
            # Send a fresh message since previous flow was text-based
            show_dashboard(bot, message, shop) 
        else:
            bot.send_message(message.chat.id, "❌ Error saving product.")

    # ==========================
    # ✏️ EDIT INFO FLOW
    # ==========================
    
    @bot.callback_query_handler(func=lambda c: c.data == "shop_edit_info")
    def start_edit_info(call):
        msg = bot.send_message(
            call.message.chat.id,
            "📝 <b>Edit Description</b>\n\n"
            "Send the new description for your shop:"
        )
        bot.register_next_step_handler(msg, process_edit_desc, bot)

    def process_edit_desc(message, bot):
        new_desc = message.text
        if update_shop_desc(message.from_user.id, new_desc):
            bot.send_message(message.chat.id, "✅ Description Updated!")
            
            shop = get_shop(message.from_user.id)
            show_dashboard(bot, message, shop)
        else:
            bot.send_message(message.chat.id, "❌ Error updating.")

    # ==========================
    # 🏗 CREATE SHOP LOGIC
    # ==========================
    def process_create_shop(message, bot):
        name = message.text
        if not name or len(name) > 30:
            bot.send_message(message.chat.id, "❌ Invalid name (Max 30 chars). Try again.")
            return

        if create_shop(message.from_user.id, name):
            bot.send_message(message.chat.id, f"✅ <b>Success!</b>\n\n'{name}' is now live.")
            # Trigger dashboard manually
            shop = get_shop(message.from_user.id)
            show_dashboard(bot, message, shop)
        else:
            bot.send_message(message.chat.id, "❌ Error creating shop.")
