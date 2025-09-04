from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_basket = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Оформить заказ", callback_data="proceed_to_payment")
        ],
    ]
)
