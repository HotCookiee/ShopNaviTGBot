from aiogram.fsm.state import StatesGroup, State


class UserInfo(StatesGroup):
    number = State()
    email = State()
    delivery_address = State()
    change_email = State()
    change_address = State()


class ContactingSupport(StatesGroup):
    UserMessage = State()


class Admin(StatesGroup):
    InputSQLCommand = State()
    AnswerAdminFromSupport = State()
    GetIDProduct = State()
    Choice = State()


class AddProduct(StatesGroup):
    ProductName = State()
    ProductDescription = State()
    ProductPrice = State()
    ProductCategory = State()
    ProductPhoto = State()
    ProductQuantity = State()
