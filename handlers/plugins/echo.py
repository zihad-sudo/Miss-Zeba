# এটি একটি প্লাগিন ফাইলের উদাহরণ
def register_handlers(bot):
    
    @bot.message_handler(commands=['hello'])
    def echo_hello(message):
        bot.reply_to(message, "👋 Hello from dynamic plugin!")
