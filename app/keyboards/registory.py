from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

registry_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Войти по номеру телефона", request_contact=True)],
        [KeyboardButton(text="ℹ️ Информация о нас")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)
