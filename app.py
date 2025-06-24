import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Конфигурация (токен берется из переменных окружения)
TOKEN = os.environ['TELEGRAM_TOKEN']
BOT_USERNAME = '@your_bot_username'  # Замените на реальный username

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я работаю на хостинге Render! 🚀')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Список команд:\n/start - приветствие\n/help - помощь\n/custom - ваша команда')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Это кастомная команда!')

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text.lower()
    
    if message_type == 'private':
        if 'привет' in text:
            await update.message.reply_text('И тебе привет! 👋')
        elif 'пока' in text:
            await update.message.reply_text('До свидания! ✨')
        else:
            await update.message.reply_text('Не понимаю команду... Попробуйте /help')

# Обработка ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error: {context.error}')

# Инициализация приложения
def main():
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()
    
    # Регистрация команд
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    
    # Регистрация обработчика сообщений
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Обработка ошибок
    app.add_error_handler(error)
    
    # Опрос сервера Telegram
    print('Polling...')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()