from typing import Any
from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from ..DB.table_data_base import Order
from aiogram.fsm.context import FSMContext
from copy import deepcopy


async def navigation(
    name_select_object: str,
    name_list_object: str,
    action: str,
    state: FSMContext,
    keyboard: InlineKeyboardMarkup,
) -> tuple[InlineKeyboardMarkup, Any]:

    data = await state.get_data()
    select_object = data.get(name_select_object, 0)
    list_object = data.get(name_list_object, [])
    
    if not isinstance(list_object, (list, tuple)) or len(list_object) == 0:
        raise ValueError("Список объектов пуст или не является списком/кортежем")

    match action:
        case "next":
            if select_object < len(list_object) - 1:
                select_object += 1
            else:
                raise IndexError("Выход за пределы")
            
        case "prev":
            if select_object > 0:
                select_object -= 1
            else:
                raise IndexError("Выход за пределы")
            
        case"show_first":
            select_object = 0

        case"show_last":
            select_object = len(list_object) - 1
            
        case _:
            raise ValueError("An unknown team has been selected")

    await state.update_data({name_select_object: select_object})

    pages_btn = InlineKeyboardButton(
        text=f"{select_object + 1}-{len(list_object)}",
        callback_data="None"
    )

    rows = deepcopy(keyboard.inline_keyboard) if getattr(keyboard, "inline_keyboard", None) is not None else []

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, pages_btn)
    else:
        rows[1][1] = pages_btn

    copy_keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    return copy_keyboard, list_object[select_object]