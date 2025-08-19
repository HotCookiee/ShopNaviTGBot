from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

the_main_menu_of_the_catalog_reply = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="🧺 Корзина")],
        [KeyboardButton(text="⬅️ Выйти в главное меню")]
    ],
    resize_keyboard=True
)

product_template = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="+🛒", callback_data="add_to_cart"),
         InlineKeyboardButton(text='🔄', callback_data="update_new_category"), ],
        [InlineKeyboardButton(text="⬅️", callback_data="back"), InlineKeyboardButton(text="➡️", callback_data="next")]
    ]
)

add_to_cart_button = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="+1", callback_data="add_to_cart_plus_1"),
        InlineKeyboardButton(text='+5', callback_data="add_to_cart_plus_5"),
        InlineKeyboardButton(text='+10', callback_data="add_to_cart_plus_10"),
    ],
    [
        InlineKeyboardButton(text='Выбрать своё количество', callback_data="input_quantity")
    ],
    [
    InlineKeyboardButton(text='❌', callback_data="cancellation")
    ]
])

