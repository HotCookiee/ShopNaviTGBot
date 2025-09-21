import re
import uuid
from datetime import datetime
from decimal import Decimal

import yookassa
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardButton
from sqlalchemy.sql import delete, insert, select
from yookassa import Payment, Configuration

from ..db.connection import Database 
from ..db.table_data_base import Order, OrderItems, CartItems, Product
from ..handlers.basket import get_basket
from ..config import PAY_API_KEY_CONF
from ..keyboards.payment import payment_main, payment_info_keyboard
from ..config import SHOP_ID_CONF , SECRET_KEY_CONF

router_payment = Router()


@router_payment.message(F.text == "✅ Оформление заказа")
async def payment_message(message: Message, state: FSMContext,bot: Bot):
    user_cart = await get_info_from_user_cart(state=state)

    if len(user_cart) > 0: 
        url = await payment_success(chat_id=message.chat.id, user_id=message.from_user.id, state=state)
        new_but = InlineKeyboardButton(text="Перейти на страницу оплаты", url=url[0])
        payment_main.inline_keyboard[1][0] = new_but
        await  bot.send_invoice(
            chat_id=message.chat.id,
            title="Выберете способ оплаты",
            description="Если у вас не работает кнопка оплатить через телеграм, перейдите по ссылке для оплаты.",
            payload="case_123",
            provider_token=PAY_API_KEY_CONF,
            currency="RUB",
            prices=user_cart,
            start_parameter="buy_case",
            reply_markup=payment_main
        )
    else:
        await message.answer("Нельзя оформить покупку с пустой корзиной!")



@router_payment.callback_query(F.data == "proceed_to_payment")
async def payment_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await payment_message(callback.message, state=state, bot=bot)

async def get_user_cart(user_id: int, message: Message):
    user_cart = await get_basket(user_id)
    user_check = f"Товары которые вы хотите приобрести: {user_cart}"
    try:
        await message.edit_text(user_check, reply_markup=payment_info_keyboard, parse_mode="Markdown")
    except:
        await message.answer(user_check, reply_markup=payment_info_keyboard, parse_mode="Markdown")


@router_payment.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router_payment.callback_query(F.data == "check_payment")
async def check_payment_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get("PaymentID")
    if not payment_id:
        await callback.message.answer("Платёж не найден. Попробуйте ещё раз.")
        await callback.answer()
        return

    try:
        pay = yookassa.Payment.find_one(payment_id)  # позиционный аргумент
    except:
        await callback.message.answer("Не удалось проверить платёж. Попробуйте позже.")
        await callback.answer()
        return

    if getattr(pay, "status", None) == "succeeded":
        await callback.message.answer("✅ Последняя оплата прошла успешно!")
        await add_result_from_db(
            state=state,
            total_amount=data.get("AmountRubles") or "0.00",
        )
    else:
        await callback.message.answer("Оплата пока не завершена. Попробуйте позже.")

    await callback.answer()


@router_payment.message(F.successful_payment)
async def payment_success_from_telegram(message: Message, state: FSMContext):
    payment_info = message.successful_payment
    await add_result_from_db(state=state, total_amount=str(payment_info.total_amount))
    await message.answer(
        "Покупка успешно совершена.В течении 40 дней доставка товар будет доставлен в ближайший ПВЗ от указанного адреса.\nПри доставке вам позвонят")


def format_rub_from_kopecks(kopecks: int) -> str:
    return f"{Decimal(kopecks) / Decimal(100):.2f}"


async def payment_success(chat_id: int, user_id: int, state: FSMContext) -> tuple | None:
    id_key = str(uuid.uuid4())
    Configuration.account_id = SHOP_ID_CONF
    Configuration.secret_key = SECRET_KEY_CONF

    user_cart = await get_info_from_user_cart(state=state)
    total_kopecks = sum(x.amount for x in user_cart)
    total_rub_str = format_rub_from_kopecks(total_kopecks)

    try:
        payment = Payment.create({
            "amount": {"value": total_rub_str, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/ShopNaviBot"},
            "capture": True,
            "description": "Оплата",
            "metadata": {"chat_id": chat_id, "user_id": user_id}
        }, id_key)

        await state.update_data(
            PaymentID=payment.id,
            AmountKopecks=total_kopecks,
            AmountRubles=total_rub_str,
        )

        return payment.confirmation.confirmation_url, payment.id
    except Exception as e:
        print(f"Ошибка при создании платежа: {e}")
        return None


async def add_result_from_db(state: FSMContext, total_amount: str):
    data = await state.get_data()
    async with Database().get_session() as session:
        try:
 
            result_user_cart = await session.execute(
                select(CartItems.product_id, CartItems.quantity, Product.price)
                .join(Product)
                .where(CartItems.user_id == data.get("user_id"))
            )
            user_cart = result_user_cart.all()
            
     
            if not user_cart:
                print(f"Корзина пользователя {data.get('user_id')} пуста")
                return
            
    
            result = await session.execute(
                insert(Order).values(
                    user_id=data.get("user_id"),
                    registration_date=datetime.now().date(),
                    delivery_address=data.get("delivery_address"),
                    total_amount=total_amount
                ).returning(Order.id) 
            )
            
            order_id = result.scalar_one() 
            
 
            for product_id, quantity, price in user_cart:
                await session.execute(
                    insert(OrderItems).values(
                        order_id=order_id,
                        product_id=product_id,
                        quantity=quantity,
                        price=price
                    )
                )
            
    
            await session.execute(delete(CartItems).where(CartItems.user_id == data.get("user_id")))
            
          
            await session.commit()
            
            print(f"Заказ #{order_id} успешно создан для пользователя {data.get('user_id')}")
            return order_id 
            
        except Exception as e:
            await session.rollback()
            print(f"Ошибка при создании заказа для пользователя {data.get('user_id')}: {e}")
            raise


async def get_info_from_user_cart(state: FSMContext) -> list[LabeledPrice]:
    data = await state.get_data()

    user_cart = await get_basket(data['user_id'])
    if user_cart == "Корзина пуста.":
        return []
    products = re.findall(r"• .([\w ]+). ", user_cart)
    prices = re.findall(r"@ ([^₽@ ]+) ₽", user_cart)
    quantity = re.findall(r" — (\d+) шт.", user_cart)
    pri = []
    for prod, price, quant in zip(products, prices, quantity):
        pri.append(LabeledPrice(label=prod, amount=(int(price) * int(quant) * 100)))
    return pri
