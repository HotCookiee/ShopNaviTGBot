from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_basket = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить количество", callback_data="update_quantity"),
            InlineKeyboardButton(text="🚪 Выйти из корзины", callback_data="exit_basket")
        ],
        [
            InlineKeyboardButton(text="✅ Оформить заказ", callback_data="proceed_to_payment")
        ]
    ]
)
