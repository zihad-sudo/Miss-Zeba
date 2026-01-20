from telebot import types
from .data import get_data
from .utils import is_admin

def register_callbacks(bot):
    
    # --- UI Markups ---
    
    def get_dash_markup(chat_id):
        mk = types.InlineKeyboardMarkup(row_width=2)
        mk.add(
            types.InlineKeyboardButton("⚙️ Settings", callback_data="gm_settings"),
            types.InlineKeyboardButton("🛑 Filters", callback_data="gm_filters")
        )
        # নতুন টুলস বাটন
        mk.add(types.InlineKeyboardButton("🧰 Group Tools", callback_data="gm_tools"))
        
        mk.add(types.InlineKeyboardButton("📚 User Guide", callback_data="gm_guide"))
        mk.add(types.InlineKeyboardButton("❌ Close", callback_data="gm_close"))
        return mk

    def get_settings_markup(chat_id):
        data = get_data(chat_id)['toggles']
        mk = types.InlineKeyboardMarkup()
        btn_al = types.InlineKeyboardButton(f"{'✅' if data['antilink'] else '❌'} Anti-Link", callback_data="tog_antilink")
        btn_wel = types.InlineKeyboardButton(f"{'✅' if data['welcome'] else '❌'} Welcome", callback_data="tog_welcome")
        btn_svc = types.InlineKeyboardButton(f"{'✅' if data['service'] else '❌'} Service Del", callback_data="tog_service")
        mk.row(btn_al, btn_wel)
        mk.add(btn_svc)
        mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="open_management"))
        return mk

    def get_filters_markup(chat_id):
        data = get_data(chat_id)['toggles']
        mk = types.InlineKeyboardMarkup()
        btn_st = types.InlineKeyboardButton(f"{'✅' if data['block_sticker'] else '❌'} Block Sticker", callback_data="tog_block_sticker")
        btn_vc = types.InlineKeyboardButton(f"{'✅' if data['block_voice'] else '❌'} Block Voice", callback_data="tog_block_voice")
        mk.row(btn_st, btn_vc)
        mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="open_management"))
        return mk

    # নতুন টুলস মেনু
    def get_tools_markup(chat_id):
        data = get_data(chat_id)['tools']
        mk = types.InlineKeyboardMarkup()
        btn_dl = types.InlineKeyboardButton(f"{'✅' if data['downloader'] else '❌'} Downloader", callback_data="tool_tog_downloader")
        btn_we = types.InlineKeyboardButton(f"{'✅' if data['weather'] else '❌'} Weather", callback_data="tool_tog_weather")
        btn_sh = types.InlineKeyboardButton(f"{'✅' if data['shortener'] else '❌'} Shortener", callback_data="tool_tog_shortener")
        mk.row(btn_dl, btn_we)
        mk.add(btn_sh)
        mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="open_management"))
        return mk

    # --- Handlers ---

    @bot.callback_query_handler(func=lambda c: c.data == "open_management")
    def open_panel(c):
        if c.message.chat.type == 'private': return
        if is_admin(bot, c.message.chat.id, c.from_user.id):
            bot.edit_message_text("🛡️ **Group Management**", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=get_dash_markup(c.message.chat.id))

    @bot.callback_query_handler(func=lambda c: c.data == "gm_settings")
    def show_settings(c):
        if is_admin(bot, c.message.chat.id, c.from_user.id):
            bot.edit_message_text("⚙️ **General Settings**", c.message.chat.id, c.message.message_id, reply_markup=get_settings_markup(c.message.chat.id))

    @bot.callback_query_handler(func=lambda c: c.data == "gm_filters")
    def show_filters(c):
        if is_admin(bot, c.message.chat.id, c.from_user.id):
            bot.edit_message_text("🛑 **Media Filters**", c.message.chat.id, c.message.message_id, reply_markup=get_filters_markup(c.message.chat.id))

    # টুলস প্যানেল ওপেন
    @bot.callback_query_handler(func=lambda c: c.data == "gm_tools")
    def show_tools(c):
        if is_admin(bot, c.message.chat.id, c.from_user.id):
            bot.edit_message_text("🧰 **Group Tools Control**\nযে টুলসগুলো গ্রুপে অনুমতি দিতে চান:", c.message.chat.id, c.message.message_id, reply_markup=get_tools_markup(c.message.chat.id))

    @bot.callback_query_handler(func=lambda c: c.data == "gm_guide")
    def show_guide(c):
        if is_admin(bot, c.message.chat.id, c.from_user.id):
            txt = (
                "📚 **User Guide**\n\n"
                "**Tools Commands:**\n"
                "• `/dl <link>` - Download media.\n"
                "• `/weather <city>` - Check weather.\n"
                "• `/short <url>` - Shorten link.\n\n"
                "**Admin Commands:**\n"
                "• `/ban`, `/mute`, `/warn`, `/pin`\n"
                "• `/addword`, `/delword`, `/banlist`\n"
            )
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="open_management"))
            bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=mk)

    # সেটিংস টগল
    @bot.callback_query_handler(func=lambda c: c.data.startswith("tog_"))
    def handle_toggle(c):
        if not is_admin(bot, c.message.chat.id, c.from_user.id): return
        key = c.data.split("tog_")[1]
        data = get_data(c.message.chat.id)
        if key in data['toggles']:
            data['toggles'][key] = not data['toggles'][key]
            
            mk = get_filters_markup(c.message.chat.id) if key in ['block_sticker', 'block_voice'] else get_settings_markup(c.message.chat.id)
            try: bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=mk)
            except: pass

    # টুলস টগল
    @bot.callback_query_handler(func=lambda c: c.data.startswith("tool_tog_"))
    def handle_tool_toggle(c):
        if not is_admin(bot, c.message.chat.id, c.from_user.id): return
        key = c.data.split("tool_tog_")[1]
        data = get_data(c.message.chat.id)
        if key in data['tools']:
            data['tools'][key] = not data['tools'][key]
            try: bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=get_tools_markup(c.message.chat.id))
            except: pass

    @bot.callback_query_handler(func=lambda c: c.data == "gm_close")
    def close_panel(c):
        bot.delete_message(c.message.chat.id, c.message.message_id)
