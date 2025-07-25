import telegram

def send_alert(bot_token, chat_id, message, image_path=None):
    bot = telegram.Bot(token=bot_token)
    if image_path:
        with open(image_path, 'rb') as photo:
            bot.send_photo(chat_id=chat_id, photo=photo, caption=message)
    else:
        bot.send_message(chat_id=chat_id, text=message)