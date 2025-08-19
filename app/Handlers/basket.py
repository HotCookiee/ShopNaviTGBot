from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.sql import select

from DB.connection import Database
from DB.table_data_base import CartItems, Product
from app.keyboards.basket import main_basket
from app.keyboards.user import main_menu

router_basket = Router()


@router_basket.message(F.text == "🧺 Корзина")
async def basket(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    user_basket = await get_basket(user_id)
    await message.answer(f"Моя корзина\n\n{user_basket}", reply_markup=main_basket, parse_mode="Markdown")


async def get_basket(user_id: int) -> str:
    answer_massage = "\n"
    async with Database().get_session() as session:
        result = await session.execute(select(CartItems, Product).join(Product).where(
            CartItems.user_id == user_id
        )
        )
        products = result.fetchall()
        total = 0
        for cart_item, product in products:
            answer_massage += f"• `{product.name}` — {cart_item.quantity} шт. @ {product.price} ₽ за ед.\n"
            total += product.price * cart_item.quantity
        else:
            answer_massage += f"\n🧾 Общая сумма: *{total} ₽*"
            return answer_massage



@router_basket.callback_query(F.data == "exit_basket")
async def exit_basket(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Вы вернулись обратно в главное меню", reply_markup=main_menu, show_alert=False)



