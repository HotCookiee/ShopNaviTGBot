import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import update, select

import app.templates as templates
from ..temp_db.connection import Database
from ..temp_db.table_data_base import User, Order
from ..handlers.db_handlers import completing_the_task
from ..keyboards.user import changing_personal_data
from ..states import UserInfo
from ..keyboards.user import changing_personal_data 

router_user = Router()


@router_user.message(F.text == "👤 Мой профиль")
async def user_menu(message: Message, state: FSMContext):
    user_data = await state.get_data()
    async with Database().get_session() as session:
        result_user = await session.execute(
            select(Order).where(Order.user_id == user_data["user_id"])
        )
        user_orders = result_user.fetchall()

        fsm_data = await state.get_data()
        previous_count = fsm_data.get("orders_count", 0)

        current_count = len(user_orders)
        if current_count != previous_count:
            await state.update_data(orders_count=current_count)

    data = await state.get_data()
    answer = templates.user_msg_tpl.format(
        user_name=data.get('first_name', '—'),
        orders=data.get('orders_count', 0),
        vip_status='Нет' if data.get('vip_status') is False else 'Активен',
        number=data.get('number', '—'),
        email=data.get('email', '—'),
        delivery_address=data.get('delivery_address', '—'),
        data_registered=data.get('date_registry', '—')
    )

    await message.answer(answer, parse_mode="Markdown", reply_markup=changing_personal_data)


def check_email(email: str):
    regular = r"^[A-Za-z0-9_]+@[A-Za-z0-9_]+\.[a-z]{2,3}$"
    if re.match(regular, email):
        return True
    else:
        return False


@router_user.callback_query(F.data.in_({"change_email", "change_address", "change_notifications"}))
async def navigation_change_settings_user(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    match data:
        case "change_email":
            await state.set_state(UserInfo.change_email)
            await callback.message.answer("✉️ Введите новую почту:")
        case "change_address":
            await state.set_state(UserInfo.change_address)
            await callback.message.answer("🏠 Введите новый адрес:")
    await callback.answer()


@router_user.message(UserInfo.change_email)
async def change_email(message: Message, state: FSMContext):
    email_text = message.text.strip()

    if check_email(email_text):
        command = update(User).where(User.telegram_id == message.from_user.id).values(email=email_text)
        command = update(User).where(User.telegram_id == message.from_user.id).values(email=email_text) 

        await completing_the_task(command)
        await state.update_data(email=email_text)

        await message.answer("✅ Почта успешно обновлена!", show_alert=False)
    else:
        await message.answer(
            f"Не удалось обновить вашу почту по причине:\n❌ \"{email_text}\" — некорректный формат.\n"
            "Введите e-mail по примеру: `TestEmail@email.com`"
        )

    await state.set_state()


@router_user.message(UserInfo.change_address)
async def change_email(message: Message, state: FSMContext):
    address_text = message.text.strip()

    command = update(User).where(User.telegram_id == message.from_user.id).values(delivery_address=address_text)
    await state.update_data(delivery_address=address_text)
    await completing_the_task(command)
    await message.answer("✅ Адрес доставки успешно обновлена!")

    await state.set_state()



