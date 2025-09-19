import asyncio

from aiogram import Bot, Dispatcher
from app.config import TOKEN
from app.Handlers import main_router


bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    try:
        print("Bot started")
        dp.include_router(main_router)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
