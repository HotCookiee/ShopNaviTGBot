from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

payment_info_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Перейти к оплате", callback_data="go_payment")],
])
payment_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Оплатить внутри Telegram", pay=True)],
    [InlineKeyboardButton(text="Получить ссылку для оплаты", callback_data="go_payment_from_url"),
     InlineKeyboardButton(text="Проверить статус оплаты", callback_data="chek_payment")
     ]
])
