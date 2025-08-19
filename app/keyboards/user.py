from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Каталог товаров"),      KeyboardButton(text="🧺 Корзина")],
        [KeyboardButton(text="✅ Оформление заказа")],
        [KeyboardButton(text="💬 Поддержка"),            KeyboardButton(text="ℹ️ О нас")],
        [KeyboardButton(text="👤 Мой профиль"),          KeyboardButton(text="🚪 Выход")],
    ],
    resize_keyboard=True
)

changing_personal_data = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✉️ Изменить Email",
                callback_data="change_email"
            ),
            InlineKeyboardButton(
                text="🏠 Изменить адрес",
                callback_data="change_address"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Изменить уведомления",
                callback_data="change_notifications"
            )
        ]
    ]
)


