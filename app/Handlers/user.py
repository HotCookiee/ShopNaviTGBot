import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import update,select

from DB.table_data_base import User,Order
from DB.connection import Database
from app.Handlers.db_hendlers import completing_the_task
from app.keyboards.user import changing_personal_data
from app.states import UserInfo

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
    profile_text = (
        "👤  *МОЙ ПРОФИЛЬ*\n"
        "━━━━━━━━━━━\n"
        f"🛒 Заказов: {data.get('orders_count', 0)}\n"
        f"✨ VIP-статус: {'Нет' if data.get('vip_status') is False else 'Активен'}\n"
        "━━━━━━━━━━━\n"
        f"📛 Имя: `{data.get('first_name', '—')}`\n"
        f"📱 Телефон: `+{data.get('number', '—')}`\n"
        f"✉️ Email: `{data.get('email', '—')}`\n"
        f"🏠 Адрес доставки: `{data.get('delivery_address', '—')}`\n"
        "━━━━━━━━━━━\n"
        f"📅 Зарегистрирован: `{data.get('date_registory', '—')}`\n"
        f"🔔 Уведомления: {data.get('notification', '—')}"
    )

    await message.answer(profile_text, parse_mode="Markdown", reply_markup=changing_personal_data)


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
        case "change_notifications":
            await state.set_state(UserInfo.change_notifications)
            await callback.message.answer("🔔 Включить уведомления? Напишите `on` или `off`.")
    await callback.answer()


@router_user.message(UserInfo.change_email)
async def change_email(message: Message, state: FSMContext):
    email_text = message.text.strip()

    if check_email(email_text):
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


@router_user.message(UserInfo.change_notifications)
async def change_email(message: Message, state: FSMContext):
    notification_text = message.text.strip()

    if notification_text == "on":
        await message.answer("✅ Уведомления успешно включены!")
        await state.set_state()
    elif notification_text == "off":
        await message.answer("✅ Уведомления успешно отключены!")
        await state.set_state()
    else:
        await message.answer("❌ Некорректный ввод. Пожалуйста, введите либо “включить”, либо “выключить” уведомления.")
