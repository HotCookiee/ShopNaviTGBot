import re
from datetime import datetime
from functools import wraps

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select, update

from DB.connection import Database
from DB.table_data_base import Admin, User, SupportMessage
from app import states
from app.keyboards.admin import admin_panel_keyboard, main_admin_keyboard, moder_user_keyboard, select_user_keyboard, \
    admin_support_inline_keyboard, select_active_support_keyboard
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
            await message.answer("✨ Авторизация прошла успешно!!"
                                 "\nРады приветствовать вас в <b>Админ‑панели</b> 🛡"
                                 "\n📂 Управлять активными заявками и архивом"
                                 "\n💬 Отвечать пользователям прямо из центра поддержки"
                                 "\n🛠 Настраивать магазин и контролировать процессы",
                                 reply_markup=admin_panel_keyboard, parse_mode="HTML")
        except AdminAccessError:
            await message.answer("⛔️ У вас нет доступа к админ-панели.", reply_markup=main_menu)
        except Exception as e:
            await  message.answer(f"Возникла неизвестная ошибка: {e}", reply_markup=main_menu)


@router_admin.message(F.text == "🧮 Выполнить SQL запрос")
@check_admin
async def admin_sql(message: Message, state: FSMContext):
    await state.set_state(states.Admin.InputSQLCommand)
    await message.answer(
        "<b>Введите SQL‑запрос, соответствующий требованиям:</b>\n"
        "• Не использовать сложные запросы — только для анализа и небольшого редактирования.\n"
        "• Разрешённые команды: <code>INSERT</code>, <code>SELECT</code>, <code>UPDATE</code>\n"
        "• Для выхода напишите: <code>exit</code>\n\n"
        "<b>Доступные таблицы:</b>"
        "<code>admins</code>,"
        "<code>cart_items</code>,"
        "<code>categories</code>,"
        "<code>notifications</code>,"
        "<code>order_items</code>,"
        "<code>orders</code>,"
        "<code>products</code>,"
        "<code>support_messages</code>,"
        "<code>users.\n</code>"
        "<b>Шаблоны</b>\n"
        "<b>Select</b>\n"
        "<pre>SELECT column1, column2\nFROM table_name\nWHERE id = 123;\n</pre>"
        "<b>Update</b>\n"
        "<pre>UPDATE table_name\nSET column1 = 'new_value'\nWHERE id = 123;\n</pre>"
        "<b>Insert</b>\n"
        "<pre>INSERT INTO table_name (column1, column2)\nVALUES ('value1', 'value2');</pre>",
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
    await message.answer("Вы вышли из режима админ панели", reply_markup=main_admin_keyboard)


@router_admin.message(F.text == "📨 Поддержка")
@check_admin
async def exit_from_admin_panel(message: Message, state: FSMContext):
    await message.answer("📍 Центр поддержки Вы находитесь в административном разделе поддержки.\n"
                         "\nВыберите, с чем хотите работать прямо сейчас:"
                         "\n📂 Архив обращений — просмотр и поиск уже закрытых заявок."
                         "\n🔔 Активные обращения — заявки, которые ждут вашего ответа или действий."
                         "\n<i>Нажмите на нужный раздел, чтобы перейти к списку и продолжить работу.</i>",
                         reply_markup=admin_support_inline_keyboard,parse_mode="HTML")


@router_admin.message(F.text == "👥 Пользователи")
@check_admin
async def exit_from_admin_panel(message: Message, state: FSMContext):
    await message.answer("Выберете действия", reply_markup=moder_user_keyboard)


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

    profile_text = (
        "👤  *Профиль пользователя {user_name}*\n"
        "━━━━━━━━━━━\n"
        "🛒 Заказов: {orders}\n"
        "✨ VIP-статус: {vip_status}\n"
        "━━━━━━━━━━━\n"
        "📱 Телефон: `+{number}`\n"
        "✉️ Email: `{email}`\n"
        "🏠 Адрес доставки: `{delivery_address}`\n"
        "━━━━━━━━━━━\n"
        "📅 Зарегистрирован: `{data_registered}`\n"
    )

    answer = profile_text.format(
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

    rows = list(select_user_keyboard.inline_keyboard)

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
    answer = (
        "<b>id жалобы</b>: <code>{id_support}</code>\n"
        "<b>user_id</b>: <code>{user_telegram_id}</code>\n"
        "<b>Дата создания</b>: <code>{date_the_request_was_created}</code>\n"
        "<b>Статус обращения</b>: <code>{status_support}</code>\n"
        "<b>Обращение</b>:\n {user_request}"
    )

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

    answer = answer.format(
        id_support=str(info_support.id),
        user_telegram_id=str(info_support.user_telegram_id),
        date_the_request_was_created=str(info_support.date_the_request_was_created),
        user_request=str(info_support.user_requests),
        status_support=str(info_support.application_status)
    )
    new_button = InlineKeyboardButton(text=f"{select_support + 1}-{len(list_support)}", callback_data="None")

    rows = list(select_active_support_keyboard.inline_keyboard)

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
async def answer_admin_from_support(message: Message, state: FSMContext):
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
        await message.answer("Успешно!")
