from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, \
    KeyboardButton

from app.keyboards.user import main_menu
from app.states import UserInfo

router_register = Router()

MESSAGES = {
    "welcome_message": "🎉 Добро пожаловать в ShopNavi! Рады видеть вас здесь — вне зависимости от того, впервые вы с нами или уже постоянный покупатель 💙\n\n🛍️ В нашем магазине вас ждёт:\n\n🔥 Актуальные скидки и промо-акции\n\n📦 Удобное отслеживание заказов\n\n🎯 Персональные рекомендации\n\n💬 Быстрая поддержка и ответы на вопросы\n\n🌟 Приятные бонусы и сюрпризы\n\n🔐 Чтобы продолжить — просто нажмите «📱 Войти по номеру» внизу. Это займёт всего пару секунд и откроет полный доступ ко всем возможностям.\n\n🔒 Ваши данные под защитой — мы заботимся о безопасности и конфиденциальности 🙌\n\n🤗 Уже были у нас? Приятно вас видеть снова! Только начинаете? Всё покажем и подскажем 😉\n\nПриятных покупок и хорошего настроения!",
    "authorization_message": "🙌 С возвращением! Рады снова видеть вас в ShopNavi 💙\n\n📦 Ваш кабинет готов:\n\nПросматривайте свои заказы и статусы доставки\n\nПолучайте персональные скидки и рекомендации\n\nОбщайтесь напрямую с поддержкой\n\nСледите за любимыми товарами и новинками\n\n💡 Не забывайте — для вас всегда действуют специальные предложения 😉\n\nПриятных покупок и отличного настроения! 🎉"
}

registry_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Войти по номеру телефона", request_contact=True)],
        [KeyboardButton(text="ℹ️ Информация о нас")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


@router_register.message(F.contact)
async def register_contact(message: Message):


    UserInfo.number = message.contact.phone_number
    UserInfo.last_name = message.contact.last_name
    UserInfo.first_name = message.contact.first_name
    UserInfo.password = message.contact.user_id


    await message.answer(MESSAGES['authorization_message'], reply_markup=main_menu)


@router_register.message(CommandStart())
async def navigation(message: Message):
    await message.answer(MESSAGES["welcome_message"], reply_markup=registry_reply_keyboard)
