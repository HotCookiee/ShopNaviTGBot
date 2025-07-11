import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import TOKEN
from routers import main_router
from app.Handlers.db_hendlers import add_user

bot = Bot(token=TOKEN)
dp = Dispatcher()

commands = [
    BotCommand(command="catalog", description="🛒 Каталог товаров"),
    BotCommand(command="cart", description="🧺 Моя корзина"),
    BotCommand(command="checkout", description="✅ Оформление заказа"),
    BotCommand(command="support", description="💬 Поддержка"),
    BotCommand(command="about", description="ℹ️ О нас"),
    BotCommand(command="profile", description="👤 Мой профиль"),
    BotCommand(command="exit", description="🚪 Выход"),
]


async def main():
    try:
        print("Bot started")
        dp.include_router(main_router)
        await add_user()
        await bot.set_my_commands(commands)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
