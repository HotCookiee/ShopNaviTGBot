import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message

from app.keyboards.user import changing_personal_data
from app.states import UserInfo

router_user = Router()


@router_user.message(F.text == "👤 Мой профиль")
async def user_menu(message: Message):
    await message.answer(f"""👤  МОЙ ПРОФИЛЬ
━━━━━━━━━━━━━━━━━━━━━━━
🛒 Заказов: 
✨ VIP-статус: {"None" if UserInfo.vip_status is State else UserInfo.vip_status}
━━━━━━━━━━━━━━━━━━━━━━━
📛 Имя:     {UserInfo.last_name}
📱 Телефон: +{UserInfo.number}
✉️ Email:    {UserInfo.email}
🏠 Адрес доставки:  {UserInfo.delivery_address}

━━━━━━━━━━━━━━━━━━━━━━━
📅 Зарегистрирован: 
🔔 Уведомления: 
""", reply_markup=changing_personal_data)


def check_email(email: str):
    regular = r"^[A-Za-z0-0_]+@[A-Za-z0-9_]+\.[a-z]{2,3}$"
    if re.match(regular, email):
        return True
    else:
        return False


@router_user.callback_query(F.data.in_({"change_email", "change_address", "change_notifications"}))
async def navigation_change_settings_user(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    match data:
        case "change_email":
            await state.set_state(UserInfo.email)
            await callback.message.answer("✉️ Введите новую почту:")
        # case "change_address":
        #     await state.set_state(UserInfo.address)
        #     await callback.message.answer("🏠 Введите новый адрес:")
        # case "change_notifications":
        #     await state.set_state(UserInfo.notifications)
        #     await callback.message.answer("🔔 Включить уведомления? Напишите `on` или `off`.")

    await callback.answer()  # убираем "часики"

# Обработка ввода новой почты
@router_user.message(UserInfo.email)
async def change_email(message: Message, state: FSMContext):
    email_text = message.text.strip()

    if check_email(email_text):
        await state.update_data(email=email_text)
        await state.clear()
        await message.answer("✅ Почта успешно обновлена!")
    else:
        await message.answer(
            f"❌ \"{email_text}\" не является корректной почтой.\n"
            "Пожалуйста, введите email по примеру: `TestEmail@email.com`"
        )
