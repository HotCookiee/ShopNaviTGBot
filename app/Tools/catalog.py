import time
from typing import Any, Sequence

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, Row

from ..temp_db.connection import Database
from ..temp_db.table_data_base import Category, Product


def decor_check_run_time(func):
    async def wrapper(*args, **kwargs):
        timer_start = time.time()
        result = await func(*args, **kwargs)
        timer_end = time.time()
        print(f"Скорость работы метода составила: {timer_end - timer_start} ")
        return result

    return wrapper


async def get_products_by_category(id_category: int) -> Sequence[Row[tuple[Product]]] | list[Any] | None:
    async with Database().get_session() as session:
        result = await  session.execute(select(Product).where(
            Product.category_id == id_category, Product.quantity > 0))


        list_products = result.scalars().all()
        if list_products:
            return list_products
        else:
            return None


async def load_keyboard_category() -> InlineKeyboardMarkup:
    main_categories = []
    async with Database().get_session() as session:
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        max_row = 3
        temp = []
        if categories:
            for category in categories:
                if max_row == 0:
                    main_categories.append(temp)
                    temp = []
                    max_row = 3

                temp.append(InlineKeyboardButton(text=category.name, callback_data=f"ID_cat_{category.id}"))
                max_row -= 1

            if temp:
                main_categories.append(temp)

            return InlineKeyboardMarkup(inline_keyboard=main_categories)
        else:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Категорий нет",
                            callback_data="no_categories"
                        )
                    ]
                ]
            )


async def get_name_category(id_category: int) -> str:
    async with Database().get_session() as session:
        result = await session.execute(select(Category.name).where(Category.id == id_category))
        name = result.scalars().first()
        return name if name else "Такой категории нет"

