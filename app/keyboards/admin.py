from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from app.keyboards.support import support_inline_keyboard

main_admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Каталог товаров"),      KeyboardButton(text="🧺 Корзина")],
        [KeyboardButton(text="✅ Оформление заказа")],
        [KeyboardButton(text="💬 Поддержка"),            KeyboardButton(text="ℹ️ О нас")],
        [KeyboardButton(text="👤 Мой профиль"),          KeyboardButton(text="🛡 Админ-панель")],
    ],
    resize_keyboard=True
)
admin_panel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧮 Выполнить SQL запрос"), KeyboardButton(text="👥 Пользователи"),KeyboardButton(text="📨 Поддержка")],
        [KeyboardButton(text="📦 Товары"), KeyboardButton(text="📋 Заказы")],
        [KeyboardButton(text="🔙 Выйти из режима")]
    ]
)
moder_user_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Найти по имени 🔎", callback_data="select_user"),InlineKeyboardButton(text="Все пользователи", callback_data="all_user")],
    ]
)
select_user_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏪", callback_data="previous_user"),InlineKeyboardButton(text="⏩", callback_data="next_user")],
    ]
)
select_active_support_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ответить",callback_data="answer_admin_from_support")],
        [InlineKeyboardButton(text="⏪", callback_data="previous_active_support"),InlineKeyboardButton(text="⏩", callback_data="next_active_support")],
    ]
)
admin_support_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Активные заявки", callback_data="active_support"),InlineKeyboardButton(text="🗄 Архив", callback_data="archive_of_applications")],
    ]
)

select_product_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Добавить новый продукт",callback_data="add_product"),InlineKeyboardButton(text="Удалить продукт по ID", callback_data="delete_product_by_id")],
    ]
)
select_products_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏪", callback_data="previous_product"),InlineKeyboardButton(text="⏩", callback_data="next_product")],
    ]
)
select_order_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text= "✅ Выполнить",callback_data="perform_order")],
        [InlineKeyboardButton(text="⏪", callback_data="previous_order"),InlineKeyboardButton(text="⏩", callback_data="next_order")],
    ]
)
confirmation_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data="confirmation_true"),InlineKeyboardButton(text="❌", callback_data="confirmation_false")],
    ]
)

continue_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="continue_true")],
    ]
)

