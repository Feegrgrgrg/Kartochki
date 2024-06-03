from aiogram import Bot, Dispatcher, executor
from config import TOKEN
from bot.handlers import send_welcome
from bot.handlers import dp

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(bot)
    dp.register_message_handler(send_welcome, commands=['start'])  # Регистрация обработчика
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)  
    
async def on_startup(_):
    print("Бот онлайн!")
    
    
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
    