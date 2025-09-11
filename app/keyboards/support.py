from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

support_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Обратиться в поддержку ", callback_data="contact_support"),
        InlineKeyboardButton(text="Мои обращения", callback_data="viewing_applications"),
    ]
])
select_support_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="⏪", callback_data="previous_complaint"),
        InlineKeyboardButton(text="⏩", callback_data="next_complaint"),
        InlineKeyboardButton(text="🚪 ", callback_data="back_to_support_main"),
    ]
])

