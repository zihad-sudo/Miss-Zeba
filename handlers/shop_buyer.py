import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils_shop import get_shop

def register_buyer_handlers(bot):

    # --- 1. LIST PRODUCTS (Browse Menu) ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("view_prods_"))
    def list_shop_products(call):
        shop_id = call.data.replace("view_prods_", "")
        shop = get_shop(shop_id)
        
        if not shop:
            bot.answer_callback_query(call.id, "❌ Shop not found.")
            return

        products = shop.get("products", {})
        
        if not products:
            bot.answer_callback_query(call.id, "📂 This shop is empty!", show_alert=True)
            return

        # Build the Menu
        kb = InlineKeyboardMarkup(row_width=1)
        for prod_id, prod_data in products.items():
            btn_text = f"{prod_data['name']} - {prod_data['price']}"
            callback = f"sh_view_{shop_id}_{prod_id}"
            kb.add(InlineKeyboardButton(btn_text, callback_data=callback))
        
        kb.add(InlineKeyboardButton("❌ Close Shop", callback_data="main_menu_return"))

        text = (
            f"🏪 <b>{shop['name']}</b>\n"
            f"📦 <b>Available Products:</b> {len(products)}\n\n"
            f"👇 <i>Click an item to see details:</i>"
        )
        
        # ✅ FIX: Handle Transition from Photo to Text
        try:
            # Attempt to edit (Works if previous message was Text)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=kb
            )
        except Exception:
            # If edit fails (e.g. coming from a Photo), Delete & Send New
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass # Ignore if already deleted
            
            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=kb
            )

    # --- 2. VIEW SINGLE PRODUCT ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("sh_view_"))
    def view_product(call):
        try:
            parts = call.data.split("_")
            # Format: sh_view_SHOPID_PRODID
            shop_id = parts[2]
            prod_id = "_".join(parts[3:]) 
            
            shop = get_shop(shop_id)
            product = shop["products"].get(prod_id)
            
            if not product:
                bot.answer_callback_query(call.id, "❌ Product unavailable.")
                return

            # Delete the menu to show the photo cleanly
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            
            caption = (
                f"📦 <b>{product['name']}</b>\n"
                f"💰 <b>Price:</b> {product['price']}\n\n"
                f"🏪 <b>Seller:</b> {shop['name']}\n"
                f"📝 <i>{shop['description']}</i>"
            )
            
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("💬 Contact Seller to Buy", url=f"tg://user?id={shop_id}"))
            # This "Back" button triggers the function above (list_shop_products)
            kb.add(InlineKeyboardButton("🔙 Back to List", callback_data=f"view_prods_{shop_id}"))

            bot.send_photo(
                call.message.chat.id,
                product['image'],
                caption=caption,
                reply_markup=kb
            )
            
        except Exception as e:
            print(f"Error viewing product: {e}")
            bot.answer_callback_query(call.id, "❌ Error loading product.")
