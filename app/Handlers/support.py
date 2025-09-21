from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.sql import insert, select

import app.templates as templates
from ..db.connection import Database
from ..db.table_data_base import SupportMessage
from ..keyboards.support import support_inline_keyboard, select_support_inline_keyboard
from ..states import ContactingSupport

router_support = Router()


@router_support.message(F.text == "💬 Поддержка")
async def support_main(message: Message):
    await message.answer(templates.user_support_info_msg, reply_markup=support_inline_keyboard)


@router_support.callback_query(F.data == "contact_support")
async def contact_support(callback_data: CallbackQuery, state: FSMContext):
    await callback_data.answer(
        "Пожалуйста опишите вашу причину максимально подробно для администрации.\nВ кротчайшие сроки вам ответят")
    await state.set_state(ContactingSupport.UserMessage)


@router_support.message(ContactingSupport.UserMessage)
async def contact_support_start(message: Message, state: FSMContext):
    async with Database().get_session() as session:
        command = insert(SupportMessage).values(
            user_requests=message.text,
            user_telegram_id=message.from_user.id,
        )
    await session.execute(command)
    await session.commit()
    await message.delete()
    await message.answer("Обращение успешно создано.\nОжидайте вам скоро ответят")
    await message.answer("Поддержка пользователей", reply_markup=support_inline_keyboard)
    await state.set_state(None)


@router_support.callback_query(F.data == "viewing_applications")
async def viewing_applications(callback_data: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(SelectSupport=0)

    async with Database().get_session() as session:
        result_select_complaint_quantity = await session.execute(select(SupportMessage).where(
            SupportMessage.user_telegram_id == data.get("telegram_id")
        ))
        complaint = result_select_complaint_quantity.scalars().all()
        await state.update_data(ListSupport=complaint)
    await callback_data.message.edit_text(
        text=templates.support_user_msg_tpl.format(
            support_id=f"`{complaint[0].id}`",
            support_state=f"`{complaint[0].application_status}`",
            date_the_request_was_created=f"`{complaint[0].date_the_request_was_created}`",
            time_answer=f"`{complaint[0].time_answer if complaint[0].time_answer is not None else '-'}`",
            user_requests=f"`{complaint[0].user_requests}`",
            admin_answer=f"`{complaint[0].admin_answer if complaint[0].admin_answer is not None else '-'}`"
        ),
        reply_markup=select_support_inline_keyboard,
        parse_mode="Markdown"
    )


@router_support.callback_query(F.data == "next_complaint")
async def next_complaint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    complaints = data.get("ListSupport", [])
    old_page_support = data.get("SelectSupport", 0)

    new_page_support = min(old_page_support + 1, len(complaints) - 1)

    # Проверка на повтор
    if new_page_support != old_page_support:
        await state.update_data(SelectSupport=new_page_support)
        await edit_the_complaint(callback, state)
    else:
        await callback.answer("")


@router_support.callback_query(F.data == "previous_complaint")
async def previous_complaint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    old_page_support = data.get("SelectSupport", 0)

    new_page_support = max(old_page_support - 1, 0)

    # Проверка на повтор
    if new_page_support != old_page_support:
        await state.update_data(SelectSupport=new_page_support)
        await edit_the_complaint(callback, state)
    else:
        await callback.answer("")


async def edit_the_complaint(callback_data: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    complaint = data["ListSupport"]
    new_page_support = data.get("SelectSupport")
    await callback_data.message.edit_text(
        text=templates.support_user_msg_tpl.format(
            support_id=f"`{complaint[new_page_support].id}`",
            support_state=f"`{complaint[new_page_support].application_status}`",
            date_the_request_was_created=f"`{complaint[new_page_support].date_the_request_was_created}`",
            time_answer=f"`{complaint[new_page_support].time_answer if complaint[new_page_support].time_answer is not None else '-'}`",
            user_requests=f"`{complaint[new_page_support].user_requests}`",
            admin_answer=f"`{complaint[new_page_support].admin_answer if complaint[new_page_support].admin_answer is not None else '-'}`"
        ),
        reply_markup=select_support_inline_keyboard,
        parse_mode="Markdown"
    )

@router_support.callback_query(F.data == "back_to_support_main")
async def back_to_support_main(callback_data: CallbackQuery, state: FSMContext):
    await callback_data.message.edit_text(templates.user_support_info_msg, reply_markup=support_inline_keyboard)