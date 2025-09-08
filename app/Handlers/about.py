from aiogram import Router,F
from aiogram.types import Message
import app.templates as templates


router_about = Router()

@router_about.message(F.text.in_({"ℹ️ О нас", "ℹ️ Информация о нас"}))
async def exit_about(message: Message):
    await message.answer(text=templates.shop_info_msg)