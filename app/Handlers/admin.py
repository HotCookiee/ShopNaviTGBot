import re
from collections.abc import Sequence
from datetime import datetime
from functools import wraps

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, update, delete

import app.keyboards.admin as admin_keyboards
import app.states as states
import app.templates as templates
from DB.connection import Database
from DB.table_data_base import Admin, User, SupportMessage, Product, Order, OrderItems
from app.keyboards.user import main_menu

router_admin = Router()


class AdminAccessError(Exception):
    """Ошибки связанные с администратором"""

    def __init__(self, message="Верификация не пройдена"):
        super().__init__(message)


def check_admin(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
        data = await state.get_data()

        if data.get("role") == 'admin':
            async with Database().get_session() as session:
                result = await session.execute(select(Admin).where(Admin.telegram_id == message.from_user.id))
                validate_admin = result.scalar_one_or_none()
                if validate_admin is not None:
                    return await func(message, state, *args, **kwargs)

        await message.answer(text="У вас недостаточно прав для выполнения этой команды.")
        return None

    return wrapper


@router_admin.message(F.text == "🛡 Админ-панель")
async def admin(message: Message, state: FSMContext):
    await verifying_access_from_the_user(message, state)


async def verifying_access_from_the_user(message: Message, state: FSMContext):
    data = await state.get_data()
    async with Database().get_session() as session:
        result_check = await session.execute(
            select(Admin).
            where(
                Admin.id == data.get('admin_id'),
            ))
        try:
            result = result_check.scalar_one_or_none()
            if result is None or result.telegram_id != message.from_user.id:
                raise AdminAccessError()
            await message.answer(templates.welcome_admin_msg,
                                 reply_markup=admin_keyboards.admin_panel_keyboard, parse_mode="HTML")
        except AdminAccessError:
            await message.answer(templates.not_admin_msg, reply_markup=main_menu)
        except Exception as e:
            await  message.answer(templates.error_msg_tpl.format(error=e), reply_markup=main_menu)


@router_admin.message(F.text == "🧮 Выполнить SQL запрос")
@check_admin
async def admin_sql(message: Message, state: FSMContext):
    await state.set_state(states.Admin.InputSQLCommand)
    await message.answer(
        templates.sql_commands_info_msg,
        parse_mode="HTML"
    )


@router_admin.message(states.Admin.InputSQLCommand)
async def input_sql_command(message: Message, state: FSMContext):
    check_delete = r"delete+"

    matches = re.findall(check_delete, message.text, flags=re.IGNORECASE)

    if message.text == "exit":
        await message.answer("Вы успешно вышли из записи SQL запроса")
        await state.set_state()
        return
    if matches:
        await message.answer(f"⚠ Найдено запрещённое слово: {matches}\n")
    else:
        await state.update_data(InputSQLCommand=message.text)
        await execute_sql_command(message, state)
        await state.set_state()


async def execute_sql_command(message: Message, state: FSMContext):
    data = await state.get_data()
    sql_command = text(data.get("InputSQLCommand"))
    try:
        async with Database().get_session() as session:
            result_check = await session.execute(sql_command)
            result = result_check.fetchall()
            result_answer = ""
            for i in result:
                result_answer += f"\n{i}"
            await message.answer(f"Команда выполнена успешно: {result_answer}")
    except Exception as e:
        await message.answer(f"При выполнении команды:{sql_command} произошла ошибка:{e}")
    await state.set_state()


@router_admin.message(F.text == "🔙 Выйти из режима")
@check_admin
async def exit_from_admin_panel(message: Message, state: FSMContext):
    await state.set_state()
    await message.answer("Вы вышли из режима админ панели", reply_markup=admin_keyboards.main_admin_keyboard)


@router_admin.message(F.text == "📨 Поддержка")
@check_admin
async def exit_from_admin_panel(message: Message,state: FSMContext):
    await message.answer(templates.welcome_admin_msg,
                         reply_markup=admin_keyboards.admin_support_inline_keyboard, parse_mode="HTML")


@router_admin.message(F.text == "👥 Пользователи")
@check_admin
async def exit_from_admin_panel(message: Message,state: FSMContext):
    await message.answer(text= "Пока вы можете просматривать всех пользователей 😅", reply_markup=admin_keyboards.moder_user_keyboard)


@router_admin.message(F.text == "📦 Товары")
async def exit_from_admin_panel(message: Message):
    await message.answer(text= templates.admin_basket, reply_markup=admin_keyboards.select_product_keyboard,parse_mode='HTML')


@router_admin.message(F.text == "📋 Заказы")
@check_admin
async def exit_from_admin_panel(message: Message, state: FSMContext):
    async with Database().get_session() as session:
        list_order_result = await session.execute(
            select(Order).order_by(Order.status))
    await state.update_data(ListOrder=list_order_result.scalars().all())
    await state.update_data(SelectOrder=0)
    data = await state.get_data()
    one_order: Order = data["ListOrder"][data["SelectOrder"]]
    answer = templates.order_msg_tpl.format(
        id=one_order.id,
        user_id=one_order.user_id,
        registration_date=one_order.registration_date,
        status=one_order.status,
        total_amount=one_order.total_amount
    )
    await message.answer(text=answer, parse_mode="HTML", reply_markup=admin_keyboards.select_order_keyboard)




@router_admin.callback_query(F.data.in_({"perform_order"}))
async def perform_order(query: CallbackQuery, state: FSMContext):
    state = await state.get_data()
    async with Database().get_session() as session:
        order: Order = state["ListOrder"][state["SelectOrder"]]
        if order.status == "Выполнено":
            await query.answer("Заказ уже выполнен")
            return

        await session.execute(update(Order).where(Order.id == order.id).values(status="Выполнено"))
        await session.commit()
        await query.answer("✅ Заказ выполнен ")


@router_admin.callback_query(F.data.in_({"previous_order", "next_order"}))
async def order_navigation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    select_order = data.get("SelectOrder", 0)
    total_orders = len(data.get("ListOrder", []))

    if callback.data == "next_order":
        if select_order < total_orders - 1:
            select_order += 1
        else:
            await callback.answer("Выход за пределы", show_alert=False)
            return
    else:
        if select_order > 0:
            select_order -= 1
        else:
            await callback.answer("Выход за пределы", show_alert=False)
            return
    await state.update_data(SelectOrder=select_order)
    data = await state.get_data()
    select_order = data.get("SelectOrder")
    list_order = data.get("ListOrder")
    order: Order = list_order[select_order]
    answer = templates.order_msg_tpl.format(
        id=order.id,
        user_id=order.user_id,
        registration_date=order.registration_date,
        status=order.status,
        total_amount=order.total_amount
    )
    new_button = InlineKeyboardButton(
        text=f"{select_order + 1}-{len(data.get('ListOrder'))}",
        callback_data="None"
    )
    rows = list(admin_keyboards.select_order_keyboard.inline_keyboard)

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, new_button)
    else:
        rows[1][1] = new_button

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        text=answer,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router_admin.callback_query(F.data.in_({"all_user", "previous_user", "next_user"}))
async def view_all_users(callback: CallbackQuery, state: FSMContext):
    if callback.data == "all_user":
        async with Database().get_session() as session:
            get_full_users = await session.execute(
                select(User).options(selectinload(User.orders)).order_by(User.id)
            )
            await state.update_data(ListUser=get_full_users.scalars().all())
            await state.update_data(SelectUser=0)
    elif callback.data in ["previous_user", "next_user"]:
        data = await state.get_data()
        select_user = data.get("SelectUser", 0)
        total_users = len(data.get("ListUser", []))

        if callback.data == "next_user":
            if select_user < total_users - 1:
                select_user += 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return
        else:
            if select_user > 0:
                select_user -= 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return

        await state.update_data(SelectUser=select_user)

    data = await state.get_data()
    select_user = data.get("SelectUser")
    list_user = data.get("ListUser")
    user: User = list_user[select_user]

    answer = templates.user_msg_tpl.format(
        user_name=user.first_name,
        orders=len(user.orders),
        vip_status=user.vip_status,
        number=user.number,
        email=user.email,
        delivery_address=user.delivery_address,
        data_registered=user.date_registory
    )
    new_button = InlineKeyboardButton(
        text=f"{select_user + 1}-{len(data.get('ListUser'))}",
        callback_data="None"
    )

    rows = list(admin_keyboards.select_user_keyboard.inline_keyboard)

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, new_button)
    else:
        rows[1][1] = new_button

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        text=answer,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router_admin.callback_query(
    F.data.in_({"active_support", "archive_of_applications", "previous_active_support", "next_active_support"}))
async def view_active_support(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback.data in {"active_support", "archive_of_applications"}:
        async with Database().get_session() as session:
            if callback.data == "active_support":
                query = (
                    select(SupportMessage)
                    .where(SupportMessage.application_status == "В обработке")
                    .order_by(SupportMessage.date_the_request_was_created.desc())
                )
            else:
                query = select(SupportMessage).order_by(SupportMessage.date_the_request_was_created.desc())

            execute_command = await session.execute(query)
            active_tickets = execute_command.scalars().all()

            await state.update_data(ListSupport=active_tickets)
            await state.update_data(SelectSupport=0)
    else:
        select_support = data.get("SelectSupport", 0)
        list_support = data.get("ListSupport", [])

        if callback.data == "next_active_support":
            if select_support < len(list_support) - 1:
                select_support += 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return
        else:
            if select_support > 0:
                select_support -= 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return

        await state.update_data(SelectSupport=select_support)

    data = await state.get_data()
    select_support = data.get("SelectSupport")
    list_support = data.get("ListSupport")
    info_support = list_support[select_support]

    answer = templates.support_admin_msg_tpl.format(
        id_support=str(info_support.id),
        user_telegram_id=str(info_support.user_telegram_id),
        date_the_request_was_created=str(info_support.date_the_request_was_created),
        user_request=str(info_support.user_requests),
        status_support=str(info_support.application_status)
    )
    new_button = InlineKeyboardButton(text=f"{select_support + 1}-{len(list_support)}", callback_data="None")

    rows = list(admin_keyboards.select_active_support_keyboard.inline_keyboard)

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, new_button)
    else:
        rows[1][1] = new_button

    temp_keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        text=answer,
        parse_mode="HTML",
        reply_markup=temp_keyboard
    )


@router_admin.callback_query(F.data == "answer_admin_from_support")
async def answer_admin_from_support(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users_complaint: SupportMessage = data.get("ListSupport")[data.get("SelectSupport")]
    if users_complaint.application_status == "В обработке":
        await callback.message.answer(
            "✏ Пожалуйста, введите текст ответа для пользователя.\n"
            "После отправки бот доставит его адресату в рамках этой заявки.\n"
            "Для отмены — cancel answer"
        )
        await state.set_state(states.Admin.AnswerAdminFromSupport)
    else:
        await callback.answer("Нельзя ответить на это сообщение", show_alert=False)


@router_admin.message(states.Admin.AnswerAdminFromSupport)
async def answer_admin_from_support(message: Message, state: FSMContext, bot: Bot):
    if message.text == "cancel answer":
        await message.edit_text(text="Вы вышли из режима ответов на обращения")
        return
    data = await state.get_data()

    users_complaint: SupportMessage = data.get("ListSupport")[data.get("SelectSupport")]
    async with Database().get_session() as session:
        get_admin_id = await session.execute(
            select(Admin.id).
            where(Admin.telegram_id == message.from_user.id))
        admin_id = get_admin_id.scalar()
        time_answer = datetime.today()
        admin_answer = message.text

        answer = {
            "admin_id": admin_id,
            "time_answer": time_answer,
            "admin_answer": admin_answer,
            "application_status": "Закрыто"
        }
        await session.execute(
            update(SupportMessage).
            where(SupportMessage.id == users_complaint.id).
            values(**answer))
        await session.commit()
        await state.set_state()
        await bot.send_message(234, "123")
        await message.answer("Успешно!")


@router_admin.callback_query(F.data == "delete_product_by_id")
async def del_product_by_id(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Введите ID продукта который хотите удалить")
    await state.set_state(states.Admin.GetIDProduct)


@router_admin.callback_query(F.data == "add_product")
async def add_product(callback: CallbackQuery):
    await callback.message.edit_text(text=templates.add_product_intro_msg, parse_mode="HTML",
                                     reply_markup=admin_keyboards.continue_keyboard)


@router_admin.message(states.Admin.GetIDProduct)
async def delete_product(message: Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой ID.")
        return

    async with Database().get_session() as session:
        result = await session.execute(
            select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
        )
        product_info: Product = result.scalar_one_or_none()
        if product_info is None:
            await message.answer("Был указан несуществующий ID.")
        else:
            await state.update_data(IDDeleteTheProduct=product_id)
            answer_msg = templates.product_msg_tpl.format(id=product_info.id,
                                                          name=product_info.name,
                                                          quantity=product_info.quantity,
                                                          category=product_info.category)

            await message.answer(
                text=(
                    "<b>Вы подтверждаете удаление продукта из базы данных:</b>\n\n"
                    f"{answer_msg}\n"
                    "❗ Это действие необратимо. Подтвердите удаление:"
                ),
                reply_markup=admin_keyboards.confirmation_keyboard,
                parse_mode="HTML"
            )
        await state.set_state(states.Admin.Choice)


@router_admin.callback_query(StateFilter(states.Admin.Choice), F.data.in_({"confirmation_true", "confirmation_false"}))
async def choice(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    st = await state.get_data()
    if data == "confirmation_true":
        async with Database().get_session() as session:
            await session.execute(delete(Product).where(Product.id == st.get("IDDeleteTheProduct")))
            await callback.message.edit_text("Удаление прошло успешно",
                                             reply_markup=admin_keyboards.select_product_keyboard)
            await session.commit()
            await state.set_state()
    elif data == "confirmation_false":
        await callback.message.edit_text("Удаление отменено", reply_markup=admin_keyboards.select_product_keyboard)
        await state.set_state()
    else:
        await callback.message.answer("ERROR", reply_markup=None)


@router_admin.callback_query(F.data == "continue_true")
async def start_adding(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Этап 1: Укажите имя товара")
    await state.set_state(states.AddProduct.ProductName)


@router_admin.message(states.AddProduct.ProductName)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductName=message.text)
    await message.answer("тап 2: Укажите описание товара")
    await state.set_state(states.AddProduct.ProductDescription)


@router_admin.message(states.AddProduct.ProductDescription)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductDescription=message.text)
    await message.answer("Этап 3: Укажите цену товара")
    await state.set_state(states.AddProduct.ProductPrice)


@router_admin.message(states.AddProduct.ProductPrice)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductPrice=message.text)
    await message.answer("Этап 4: Укажите категорию товара")
    await state.set_state(states.AddProduct.ProductCategory)


@router_admin.message(states.AddProduct.ProductCategory)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductCategory=message.text)
    await message.answer("Этап 5: Отправьте фото товара")
    await state.set_state(states.AddProduct.ProductPhoto)


@router_admin.message(states.AddProduct.ProductPhoto)
async def get_name_product(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(ProductPhoto=message.photo[-1].file_id)
        await state.set_state(states.AddProduct.ProductQuantity)
        await message.answer("Этап 6: Введите количество товара")
    else:
        await message.edit_text("❗ Пожалуйста, отправьте фото как изображение, а не как файл.")

@router_admin.message(states.AddProduct.ProductQuantity)
async def get_quantity_product(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(ProductQuantity=int(message.text))
        await completion_creation(message, state)
    else:
        await message.edit_text("❗ Пожалуйста, введите число!")



async def completion_creation(message: Message, state: FSMContext):
    st = await state.get_data()
    temp_product_info = {
        "name": st.get("ProductName"),
        "description": st.get("ProductDescription"),
        "price": int(st.get("ProductPrice")),
        "category_id": int(st.get("ProductCategory")),
        "quantity": int(st.get("ProductQuantity")),
        "photo": st.get("ProductPhoto"),
    }

    async with Database().get_session() as session:
        await session.execute(insert(Product).values(**temp_product_info))
        await session.commit()

    await message.answer("Продукт успешно создан!")
    await state.set_state()


@router_admin.callback_query(F.data == "order_details")
async def order_details(callback: CallbackQuery, state: FSMContext):
    async with Database().get_session() as session:
        data = await state.get_data()
        select_order = data.get("SelectOrder")
        list_order = data.get("ListOrder")
        order: Order = list_order[select_order]
        print(order.id)
        result = await session.execute(select(OrderItems)
                                       .options(selectinload(OrderItems.product),selectinload(OrderItems.order).selectinload(Order.user))
                                       .where(OrderItems.order_id == order.id))
        items: Sequence[OrderItems] = result.scalars().all()
        products = ""

        for item in items:
            products += f"• <code>{item.product.name}</code> — <b>{item.quantity} шт. @ {item.product.price} ₽ за ед.</b>\n"
        else:
            msg_answer = templates.admin_cart_from_user_msg_tpl.format(
                user_name = items[0].order.user.first_name,
                telegram_user_id = items[0].order.user.telegram_id,
                list_products = products
            )
        await callback.message.edit_text(text = msg_answer,reply_markup=admin_keyboards.select_order_keyboard,parse_mode = "HTML")

import re
from collections.abc import Sequence
from datetime import datetime
from functools import wraps

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, update, delete

import app.keyboards.admin as admin_keyboards
import app.states as states
import app.templates as templates
from DB.connection import Database
from DB.table_data_base import Admin, User, SupportMessage, Product, Order, OrderItems
from app.keyboards.user import main_menu

router_admin = Router()


class AdminAccessError(Exception):
    """Ошибки связанные с администратором"""

    def __init__(self, message="Верификация не пройдена"):
        super().__init__(message)


def check_admin(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
        data = await state.get_data()

        if data.get("role") == 'admin':
            async with Database().get_session() as session:
                result = await session.execute(select(Admin).where(Admin.telegram_id == message.from_user.id))
                validate_admin = result.scalar_one_or_none()
                if validate_admin is not None:
                    return await func(message, state, *args, **kwargs)

        await message.answer(text="У вас недостаточно прав для выполнения этой команды.")
        return None

    return wrapper


@router_admin.message(F.text == "🛡 Админ-панель")
async def admin(message: Message, state: FSMContext):
    await verifying_access_from_the_user(message, state)


async def verifying_access_from_the_user(message: Message, state: FSMContext):
    data = await state.get_data()
    async with Database().get_session() as session:
        result_check = await session.execute(
            select(Admin).
            where(
                Admin.id == data.get('admin_id'),
            ))
        try:
            result = result_check.scalar_one_or_none()
            if result is None or result.telegram_id != message.from_user.id:
                raise AdminAccessError()
            await message.answer(templates.welcome_admin_msg,
                                 reply_markup=admin_keyboards.admin_panel_keyboard, parse_mode="HTML")
        except AdminAccessError:
            await message.answer(templates.not_admin_msg, reply_markup=main_menu)
        except Exception as e:
            await  message.answer(templates.error_msg_tpl.format(error=e), reply_markup=main_menu)


@router_admin.message(F.text == "🧮 Выполнить SQL запрос")
@check_admin
async def admin_sql(message: Message, state: FSMContext):
    await state.set_state(states.Admin.InputSQLCommand)
    await message.answer(
        templates.sql_commands_info_msg,
        parse_mode="HTML"
    )


@router_admin.message(states.Admin.InputSQLCommand)
async def input_sql_command(message: Message, state: FSMContext):
    check_delete = r"delete+"

    matches = re.findall(check_delete, message.text, flags=re.IGNORECASE)

    if message.text == "exit":
        await message.answer("Вы успешно вышли из записи SQL запроса")
        await state.set_state()
        return
    if matches:
        await message.answer(f"⚠ Найдено запрещённое слово: {matches}\n")
    else:
        await state.update_data(InputSQLCommand=message.text)
        await execute_sql_command(message, state)
        await state.set_state()


async def execute_sql_command(message: Message, state: FSMContext):
    data = await state.get_data()
    sql_command = text(data.get("InputSQLCommand"))
    try:
        async with Database().get_session() as session:
            result_check = await session.execute(sql_command)
            result = result_check.fetchall()
            result_answer = ""
            for i in result:
                result_answer += f"\n{i}"
            await message.answer(f"Команда выполнена успешно: {result_answer}")
    except Exception as e:
        await message.answer(f"При выполнении команды:{sql_command} произошла ошибка:{e}")
    await state.set_state()


@router_admin.message(F.text == "🔙 Выйти из режима")
@check_admin
async def exit_from_admin_panel(message: Message, state: FSMContext):
    await state.set_state()
    await message.answer("Вы вышли из режима админ панели", reply_markup=admin_keyboards.main_admin_keyboard)


@router_admin.message(F.text == "📨 Поддержка")
@check_admin
async def exit_from_admin_panel(message: Message,state: FSMContext):
    await message.answer(templates.welcome_admin_msg,
                         reply_markup=admin_keyboards.admin_support_inline_keyboard, parse_mode="HTML")


@router_admin.message(F.text == "👥 Пользователи")
@check_admin
async def exit_from_admin_panel(message: Message,state: FSMContext):
    await message.answer(text= "Пока вы можете просматривать всех пользователей 😅", reply_markup=admin_keyboards.moder_user_keyboard)


@router_admin.message(F.text == "📦 Товары")
async def exit_from_admin_panel(message: Message):
    await message.answer(text= templates.admin_basket, reply_markup=admin_keyboards.select_product_keyboard,parse_mode='HTML')


@router_admin.message(F.text == "📋 Заказы")
@check_admin
async def exit_from_admin_panel(message: Message, state: FSMContext):
    async with Database().get_session() as session:
        list_order_result = await session.execute(
            select(Order).order_by(Order.status))
    await state.update_data(ListOrder=list_order_result.scalars().all())
    await state.update_data(SelectOrder=0)
    data = await state.get_data()
    one_order: Order = data["ListOrder"][data["SelectOrder"]]
    answer = templates.order_msg_tpl.format(
        id=one_order.id,
        user_id=one_order.user_id,
        registration_date=one_order.registration_date,
        status=one_order.status,
        total_amount=one_order.total_amount
    )
    await message.answer(text=answer, parse_mode="HTML", reply_markup=admin_keyboards.select_order_keyboard)


#
# @router_admin.callback_query(F.data.in_({"view_ditail"}))
# async def view_ditail_order(query: CallbackQuery, state: FSMContext):
#     state = await state.get_data()
#     async with Database().get_session() as session:
#         order: Order = state["ListOrder"][state["SelectedOrder"]]
#         get_item_form_order = await session.execute(select(OrderItems).where(OrderItems.order_id == order.id))
#         items = get_item_form_order.scalars().all()

@router_admin.callback_query(F.data.in_({"perform_order"}))
async def perform_order(query: CallbackQuery, state: FSMContext):
    state = await state.get_data()
    async with Database().get_session() as session:
        order: Order = state["ListOrder"][state["SelectOrder"]]
        if order.status == "Выполнено":
            await query.answer("Заказ уже выполнен")
            return

        await session.execute(update(Order).where(Order.id == order.id).values(status="Выполнено"))
        await session.commit()
        await query.answer("✅ Заказ выполнен ")


@router_admin.callback_query(F.data.in_({"previous_order", "next_order"}))
async def order_navigation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    select_order = data.get("SelectOrder", 0)
    total_orders = len(data.get("ListOrder", []))

    if callback.data == "next_order":
        if select_order < total_orders - 1:
            select_order += 1
        else:
            await callback.answer("Выход за пределы", show_alert=False)
            return
    else:
        if select_order > 0:
            select_order -= 1
        else:
            await callback.answer("Выход за пределы", show_alert=False)
            return
    await state.update_data(SelectOrder=select_order)
    data = await state.get_data()
    select_order = data.get("SelectOrder")
    list_order = data.get("ListOrder")
    order: Order = list_order[select_order]
    answer = templates.order_msg_tpl.format(
        id=order.id,
        user_id=order.user_id,
        registration_date=order.registration_date,
        status=order.status,
        total_amount=order.total_amount
    )
    new_button = InlineKeyboardButton(
        text=f"{select_order + 1}-{len(data.get('ListOrder'))}",
        callback_data="None"
    )
    rows = list(admin_keyboards.select_order_keyboard.inline_keyboard)

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, new_button)
    else:
        rows[1][1] = new_button

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        text=answer,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router_admin.callback_query(F.data.in_({"all_user", "previous_user", "next_user"}))
async def view_all_users(callback: CallbackQuery, state: FSMContext):
    if callback.data == "all_user":
        async with Database().get_session() as session:
            get_full_users = await session.execute(
                select(User).options(selectinload(User.orders)).order_by(User.id)
            )
            await state.update_data(ListUser=get_full_users.scalars().all())
            await state.update_data(SelectUser=0)
    elif callback.data in ["previous_user", "next_user"]:
        data = await state.get_data()
        select_user = data.get("SelectUser", 0)
        total_users = len(data.get("ListUser", []))

        if callback.data == "next_user":
            if select_user < total_users - 1:
                select_user += 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return
        else:
            if select_user > 0:
                select_user -= 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return

        await state.update_data(SelectUser=select_user)

    data = await state.get_data()
    select_user = data.get("SelectUser")
    list_user = data.get("ListUser")
    user: User = list_user[select_user]

    answer = templates.user_msg_tpl.format(
        user_name=user.first_name,
        orders=len(user.orders),
        vip_status=user.vip_status,
        number=user.number,
        email=user.email,
        delivery_address=user.delivery_address,
        data_registered=user.date_registory
    )
    new_button = InlineKeyboardButton(
        text=f"{select_user + 1}-{len(data.get('ListUser'))}",
        callback_data="None"
    )

    rows = list(admin_keyboards.select_user_keyboard.inline_keyboard)

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, new_button)
    else:
        rows[1][1] = new_button

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        text=answer,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router_admin.callback_query(
    F.data.in_({"active_support", "archive_of_applications", "previous_active_support", "next_active_support"}))
async def view_active_support(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback.data in {"active_support", "archive_of_applications"}:
        async with Database().get_session() as session:
            if callback.data == "active_support":
                query = (
                    select(SupportMessage)
                    .where(SupportMessage.application_status == "В обработке")
                    .order_by(SupportMessage.date_the_request_was_created.desc())
                )
            else:
                query = select(SupportMessage).order_by(SupportMessage.date_the_request_was_created.desc())

            execute_command = await session.execute(query)
            active_tickets = execute_command.scalars().all()

            await state.update_data(ListSupport=active_tickets)
            await state.update_data(SelectSupport=0)
    else:
        select_support = data.get("SelectSupport", 0)
        list_support = data.get("ListSupport", [])

        if callback.data == "next_active_support":
            if select_support < len(list_support) - 1:
                select_support += 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return
        else:
            if select_support > 0:
                select_support -= 1
            else:
                await callback.answer("Выход за пределы", show_alert=False)
                return

        await state.update_data(SelectSupport=select_support)

    data = await state.get_data()
    select_support = data.get("SelectSupport")
    list_support = data.get("ListSupport")
    info_support = list_support[select_support]

    answer = templates.support_admin_msg_tpl.format(
        id_support=str(info_support.id),
        user_telegram_id=str(info_support.user_telegram_id),
        date_the_request_was_created=str(info_support.date_the_request_was_created),
        user_request=str(info_support.user_requests),
        status_support=str(info_support.application_status)
    )
    new_button = InlineKeyboardButton(text=f"{select_support + 1}-{len(list_support)}", callback_data="None")

    rows = list(admin_keyboards.select_active_support_keyboard.inline_keyboard)

    while len(rows) < 2:
        rows.append([])

    if len(rows[1]) <= 2:
        rows[1].insert(1, new_button)
    else:
        rows[1][1] = new_button

    temp_keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        text=answer,
        parse_mode="HTML",
        reply_markup=temp_keyboard
    )


@router_admin.callback_query(F.data == "answer_admin_from_support")
async def answer_admin_from_support(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users_complaint: SupportMessage = data.get("ListSupport")[data.get("SelectSupport")]
    if users_complaint.application_status == "В обработке":
        await callback.message.answer(
            "✏ Пожалуйста, введите текст ответа для пользователя.\n"
            "После отправки бот доставит его адресату в рамках этой заявки.\n"
            "Для отмены — cansel answer"
        )
        await state.set_state(states.Admin.AnswerAdminFromSupport)
    else:
        await callback.answer("Нельзя ответить на это сообщение", show_alert=False)


@router_admin.message(states.Admin.AnswerAdminFromSupport)
async def answer_admin_from_support(message: Message, state: FSMContext, bot: Bot):
    if message.text == "cansel answer":
        await message.edit_text(text="Вы вышли из режима ответов на обращения")
        return
    data = await state.get_data()

    users_complaint: SupportMessage = data.get("ListSupport")[data.get("SelectSupport")]
    async with Database().get_session() as session:
        get_admin_id = await session.execute(
            select(Admin.id).
            where(Admin.telegram_id == message.from_user.id))
        admin_id = get_admin_id.scalar()
        time_answer = datetime.today()
        admin_answer = message.text

        answer = {
            "admin_id": admin_id,
            "time_answer": time_answer,
            "admin_answer": admin_answer,
            "application_status": "Закрыто"
        }
        await session.execute(
            update(SupportMessage).
            where(SupportMessage.id == users_complaint.id).
            values(**answer))
        await session.commit()
        await state.set_state()
        await bot.send_message(234, "123")
        await message.answer("Успешно!")


@router_admin.callback_query(F.data == "delete_product_by_id")
async def del_product_by_id(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Введите ID продукта который хотите удалить")
    await state.set_state(states.Admin.GetIDProduct)


@router_admin.callback_query(F.data == "add_product")
async def add_product(callback: CallbackQuery):
    await callback.message.edit_text(text=templates.add_product_intro_msg, parse_mode="HTML",
                                     reply_markup=admin_keyboards.continue_keyboard)


@router_admin.message(states.Admin.GetIDProduct)
async def delete_product(message: Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой ID.")
        return

    async with Database().get_session() as session:
        result = await session.execute(
            select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
        )
        product_info: Product = result.scalar_one_or_none()
        if product_info is None:
            await message.answer("Был указан несуществующий ID.")
        else:
            await state.update_data(IDDeleteTheProduct=product_id)
            answer_msg = templates.product_msg_tpl.format(id=product_info.id,
                                                          name=product_info.name,
                                                          quantity=product_info.quantity,
                                                          category=product_info.category)

            await message.answer(
                text=(
                    "<b>Вы подтверждаете удаление продукта из базы данных:</b>\n\n"
                    f"{answer_msg}\n"
                    "❗ Это действие необратимо. Подтвердите удаление:"
                ),
                reply_markup=admin_keyboards.confirmation_keyboard,
                parse_mode="HTML"
            )
        await state.set_state(states.Admin.Choice)


@router_admin.callback_query(StateFilter(states.Admin.Choice), F.data.in_({"confirmation_true", "confirmation_false"}))
async def choice(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    st = await state.get_data()
    if data == "confirmation_true":
        async with Database().get_session() as session:
            await session.execute(delete(Product).where(Product.id == st.get("IDDeleteTheProduct")))
            await callback.message.edit_text("Удаление прошло успешно",
                                             reply_markup=admin_keyboards.select_product_keyboard)
            await session.commit()
            await state.set_state()
    elif data == "confirmation_false":
        await callback.message.edit_text("Удаление отменено", reply_markup=admin_keyboards.select_product_keyboard)
        await state.set_state()
    else:
        await callback.message.answer("ERROR", reply_markup=None)


@router_admin.callback_query(F.data == "continue_true")
async def start_adding(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Этап 1: Укажите имя товара")
    await state.set_state(states.AddProduct.ProductName)


@router_admin.message(states.AddProduct.ProductName)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductName=message.text)
    await message.answer("тап 2: Укажите описание товара")
    await state.set_state(states.AddProduct.ProductDescription)


@router_admin.message(states.AddProduct.ProductDescription)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductDescription=message.text)
    await message.answer("Этап 3: Укажите цену товара")
    await state.set_state(states.AddProduct.ProductPrice)


@router_admin.message(states.AddProduct.ProductPrice)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductPrice=message.text)
    await message.answer("Этап 4: Укажите категорию товара")
    await state.set_state(states.AddProduct.ProductCategory)


@router_admin.message(states.AddProduct.ProductCategory)
async def get_name_product(message: Message, state: FSMContext):
    await state.update_data(ProductCategory=message.text)
    await message.answer("Этап 5: Отправьте фото товара")
    await state.set_state(states.AddProduct.ProductPhoto)


@router_admin.message(states.AddProduct.ProductPhoto)
async def get_name_product(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(ProductPhoto=message.photo[-1].file_id)
    else:
        await message.answer("❗ Пожалуйста, отправьте фото как изображение, а не как файл.")
    await completion_creation(message, state)


async def completion_creation(message: Message, state: FSMContext):
    st = await state.get_data()
    temp_product_info = {
        "name": st.get("ProductName"),
        "description": st.get("ProductDescription"),
        "price": int(st.get("ProductPrice")),
        "category_id": int(st.get("ProductCategory")),
        "photo": st.get("ProductPhoto"),
    }

    async with Database().get_session() as session:
        await session.execute(insert(Product).values(**temp_product_info))
        await session.commit()

    await message.answer("Продукт успешно создан!")
    await state.set_state()


@router_admin.callback_query(F.data == "order_details")
async def order_details(callback: CallbackQuery, state: FSMContext):
    async with Database().get_session() as session:
        data = await state.get_data()
        select_order = data.get("SelectOrder")
        list_order = data.get("ListOrder")
        order: Order = list_order[select_order]
        print(order.id)
        result = await session.execute(select(OrderItems)
                                       .options(selectinload(OrderItems.product),selectinload(OrderItems.order).selectinload(Order.user))
                                       .where(OrderItems.order_id == order.id))
        items: Sequence[OrderItems] = result.scalars().all()
        products = ""

        for item in items:
            products += f"• <code>{item.product.name}</code> — <b>{item.quantity} шт. @ {item.product.price} ₽ за ед.</b>\n"
        else:
            msg_answer = templates.admin_cart_from_user_msg_tpl.format(
                user_name = items[0].order.user.first_name,
                telegram_user_id = items[0].order.user.telegram_id,
                list_products = products
            )
        await callback.message.edit_text(text = msg_answer,reply_markup=admin_keyboards.select_order_keyboard,parse_mode = "HTML")
