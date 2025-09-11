from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql import update, select

from ..DB.connection import Database
from ..DB.table_data_base import CartItems, Product
from ..Tools.catalog import load_keyboard_category, get_products_by_category, get_name_category
from ..keyboards.admin import main_admin_keyboard
from ..keyboards.catalog import the_main_menu_of_the_catalog_reply, add_to_cart_button, product_template
from ..keyboards.user import main_menu
import app.templates as templates

router_catalog = Router()



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
async def exit_catalog(message: Message, state: FSMContext):
    data = await state.get_data()
    keyboard = main_admin_keyboard if data.get("role") == "admin" else main_menu

    await message.answer(text="Вы вернулись в главное меню", reply_markup=keyboard)


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

    selected_product: Product = state_data.get("ListProduct")[selected_page - 1]
    caption = templates.product_msg_tpl.format(
        name = selected_product.name,
        id = selected_product.id,
        description = selected_product.description,
        price = selected_product.price,
        quantity = selected_product.quantity,
        category = state_data.get("Category"),
    )
    await query.answer('')

    await query.message.edit_media(InputMediaPhoto(
        media=selected_product.photo,
        caption=caption,
        parse_mode="HTML",

    ),reply_markup=product_template)


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
    new_button = InlineKeyboardButton(text=f"{selected_page}-{state_data.get("MaxPage")}",
                                      callback_data="number_page")

    product_template.inline_keyboard[1][1] = new_button

    caption = templates.product_msg_tpl.format(
        name = selected_product.name,
        id = selected_product.id,
        description = selected_product.description,
        price = selected_product.price,
        quantity = selected_product.quantity,
        category = state_data.get("Category"),
    )

    await query.answer('')
    await query.message.edit_media(InputMediaPhoto(
        media=selected_product.photo,
        caption=caption,
        parse_mode="HTML",
    ),reply_markup=product_template)


@router_catalog.callback_query(F.data == "update_new_category")
async def update_category(query: CallbackQuery):
    await query.message.delete()
    await query.answer("✅ Категория сброшена")
    await query.message.answer(
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

    quantity = query.data.split("_")[-1]
    async with Database().get_session() as session:
        user_id = state_data.get("user_id", 0)
        product_id = state_data.get("ProductID", 0)
        if quantity.isdigit():
            quantity_int = int(quantity)
            product_quantity_result = await session.execute(select(Product.quantity).where(Product.id == product_id))
            product_quantity = product_quantity_result.scalar()
            new_quantity = product_quantity - int(quantity)
            if new_quantity < 0:
                await query.answer("Вы пытаетесь добавить в корзину больше чем есть на складе.", show_alert=True)
                return
            update_quantity_from_product = update(Product).where(Product.id == product_id).values(quantity=new_quantity)
            cart_items_result = await session.execute(
                select(CartItems).where(
                    CartItems.user_id == user_id,
                    CartItems.product_id == product_id
                )
            )
            product = cart_items_result.scalars().first()

            if product:
                add_quantity = product.quantity + quantity_int

                add_product_to_cart = update(CartItems).where(
                    CartItems.id == product.id
                ).values(quantity=add_quantity)

            else:
                add_product_to_cart = insert(CartItems).values(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity_int
                )

        if add_product_to_cart is not None:
            await session.execute(add_product_to_cart)
            await session.execute(update_quantity_from_product)
            await session.commit()
            await query.answer(f"✅ Вы добавили {quantity} шт. в корзину", show_alert=True)
