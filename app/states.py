from aiogram.fsm.state import StatesGroup, State


class UserInfo(StatesGroup):
    number = State()
    lsat_name = State()
    email = State()
    vip_status = State()
    password = State()
    delivery_address = State()
    notification = State()
    role = State()
    telegram_id = State()
    date_registory = State()


