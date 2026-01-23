# মেনুতে বাটন দেখানোর জন্য এই লাইনটি বাধ্যতামূলক
TOOL_INFO = {
    "label": "🗣 Echo Tool",
    "callback": "tool_echo"
}

def register_handlers(bot):
    
    # মেনু বাটন হ্যান্ডলার
    @bot.callback_query_handler(func=lambda c: c.data == "tool_echo")
    def run_tool(call):
        bot.send_message(call.message.chat.id, "👋 Hi! This is a new tool added via Admin Panel.")

    # কমান্ড হ্যান্ডলার
    @bot.message_handler(commands=['echo'])
    def echo(m):
        bot.reply_to(m, "Echo working!")
