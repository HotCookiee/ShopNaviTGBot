from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql import update, select

from DB.connection import Database
from DB.table_data_base import CartItems
from app.Tools.catalog import load_keyboard_category, get_products_by_category, get_name_category
from app.keyboards.cotalog import the_main_menu_of_the_catalog_reply, add_to_cart_button, product_template
from app.keyboards.user import main_menu
from app.states import InputUserQuantity

router_catalog = Router()

PRODUCT_CATEGORY = "Вы выбрали категорию: {category}\n{name_product}\nОписание товара: {description}\nДоступно в количестве: {quantity}\nСтоимость: {price}"


@router_catalog.message(F.text == "🛒 Каталог товаров")
async def main_catalog(message: Message):
    await message.answer(
        text="🛍️ Добро пожаловать в каталог!",
        reply_markup=the_main_menu_of_the_catalog_reply
    )
    await message.answer(
        text="📂 Выберите категорию ниже:",
        reply_markup=await load_keyboard_category()
    )


@router_catalog.message(F.text == "⬅️ Выйти в главное меню")
async def exit_catalog(message: Message):
    await message.answer(text="Вы вернулись в главное меню", reply_markup=main_menu)


@router_catalog.callback_query(F.data.regexp(r'^ID_cat_[0-9]+$'))
async def main_catalog_callback(query: CallbackQuery, state: FSMContext):
    number_category = int(query.data.strip("_")[-1])

    list_product = await get_products_by_category(number_category)
    name_category = await get_name_category(number_category)
    max_page = len(list_product)

    await state.update_data(SelectedPage=1,
                            ProductID=list_product[0].id,
                            Category=name_category,
                            MaxPage=max_page,
                            ProductName=list_product[0].name,
                            ListProduct=list_product,
                            ProductPrice=list_product[0].price,
                            Quantity=list_product[0].quantity,
                            )

    state_data = await state.get_data()

    selected_page = state_data['SelectedPage']

    new_button = InlineKeyboardButton(text=f"{selected_page}-{max_page}",
                                      callback_data="number_page")

    if len(product_template.inline_keyboard[1]) <= 2:
        product_template.inline_keyboard[1].insert(1, new_button)
    else:
        product_template.inline_keyboard[1][1] = new_button

    selected_product = state_data.get("ListProduct")[selected_page - 1]
    new_product = PRODUCT_CATEGORY.format(
        category=state_data.get("Category"),
        description=selected_product.description,
        quantity=selected_product.quantity,
        name_product=selected_product.name,
        price=selected_product.price
    )
    await query.answer('')
    await query.message.edit_text(new_product, reply_markup=product_template)


@router_catalog.callback_query(F.data.in_(['next', 'back']))
async def viewing_products(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    selected_page = state_data['SelectedPage']
    selected_page += -1 if query.data == "back" else 1
    if selected_page < 1 or selected_page > state_data.get("MaxPage"):
        await query.answer("Выход за пределы", show_alert=True)
        return

    selected_product = state_data.get("ListProduct")[selected_page - 1]

    await state.update_data(SelectedPage=selected_page,
                            ProductID=selected_product.id,
                            ProductName=selected_product.name,
                            ProductPrice=selected_product.price,
                            Quantity=selected_product.quantity,
                            )

    new_product = PRODUCT_CATEGORY.format(
        category=state_data.get("Category"),
        description=selected_product.description,
        quantity=selected_product.quantity,
        name_product=selected_product.name,
        price=selected_product.price
    )

    new_button = InlineKeyboardButton(text=f"{selected_page}-{state_data.get("MaxPage")}",
                                      callback_data="number_page")

    product_template.inline_keyboard[1][1] = new_button
    await query.answer('')
    await query.message.edit_text(new_product, reply_markup=product_template)


@router_catalog.callback_query(F.data == "update_new_category")
async def update_category(query: CallbackQuery):
    await query.answer("✅ Категория сброшена!", show_alert=False)
    await query.message.edit_text(
        text="📂 Выберите категорию ниже:",
        reply_markup=await load_keyboard_category()
    )


@router_catalog.callback_query(F.data == "number_page")
async def number_page(query: CallbackQuery):
    await query.answer(
        text="Счётчик страниц",
        show_alert=False,
    )


@router_catalog.callback_query(F.data == "add_to_cart")
async def add_to_cart(query: CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=add_to_cart_button)


@router_catalog.callback_query(F.data == "cancellation")
async def cancellation(query: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await query.message.edit_reply_markup(reply_markup=product_template)


@router_catalog.callback_query(F.data.regexp(r'^add_to_cart_plus_[0-9]+$'))
async def add_products(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    selected_page = state_data['SelectedPage']
    selected_product = state_data.get("ListProduct")[selected_page - 1]

    quantity = query.data.split("_")[-1]
    async with Database().get_session() as session:
        end_command = None
        user_id = state_data.get("user_id", 0)
        product_id = state_data.get("ProductID", 0)
        if quantity.isdigit():
            quantity_int = int(quantity)

            result = await session.execute(
                select(CartItems).where(
                    CartItems.user_id == user_id,
                    CartItems.product_id == product_id
                )
            )
            product = result.scalars().first()

            if product:
                new_quantity = product.quantity + quantity_int

                end_command = update(CartItems).where(
                    CartItems.id == product.id
                ).values(quantity=new_quantity)

                print(f"Вы увеличили этот товар в своей корзине на {quantity}")
            else:
                end_command = insert(CartItems).values(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity_int
                )
                print(f"Это новый товар в вашей корзине")

        if end_command is not None:
            await session.execute(end_command)
            await session.commit()


