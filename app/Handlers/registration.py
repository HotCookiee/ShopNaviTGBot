from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, \
    KeyboardButton, InlineKeyboardMarkup,InlineKeyboardButton
from sqlalchemy import select
from pprint import pprint

from DB.connection import Database
from DB.table_data_base import User, Admin
from app.keyboards.user import main_menu
from app.keyboards.admin import main_admin_keyboard
import app.templates as templates
import app.keyboards.registory as keyboards_registration

router_register = Router()



@router_register.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):
    await get_or_create_user_and_fill_userinfo(message, state)




@router_register.message(CommandStart())
async def navigation(message: Message):
    await message.answer(templates.welcome_msg, reply_markup=keyboards_registration.registry_reply_keyboard)


async def get_or_create_user_and_fill_userinfo(message: Message, state: FSMContext) -> User:
    telegram_id = message.contact.user_id
    phone_number = message.contact.phone_number
    first_name = message.contact.first_name

    async with Database().get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        db_user = result.scalar_one_or_none()

        admin_result = await session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )

        is_admin = admin_result.scalar_one_or_none()
        if db_user is None:
            db_user = User(
                telegram_id=telegram_id,
                number=phone_number,
                first_name=first_name,
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

    payload = {
        "telegram_id": db_user.telegram_id,
        "user_id" : db_user.id,
        "admin_id" : is_admin.id if is_admin is not None else None,
        "number": db_user.number,
        "first_name": db_user.first_name,
        "email": db_user.email,
        "date_registory": db_user.date_registory,
        "vip_status": db_user.vip_status,
        "delivery_address": db_user.delivery_address,
        "role": "admin" if is_admin else "user",
        "ChatID": message.chat.id,
    }
    await state.update_data(**payload)
    await message.answer(templates.authorization_msg, reply_markup= main_admin_keyboard if is_admin is not None else main_menu)
    return db_user
