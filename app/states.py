from aiogram.fsm.state import StatesGroup, State


class UserInfo(StatesGroup):
    number = State()
    ChatID = State()
    user_id = State()
    admin_id = State()
    first_name = State()
    email = State()
    vip_status = State()
    password = State()
    delivery_address = State()
    notification = State()
    role = State()
    telegram_id = State()
    date_registory = State()
    change_email = State()
    change_address = State()
    change_notifications = State()


class ProductFlow(StatesGroup):
    ProductID = State()
    ProductName = State()
    ProductPrice = State()
    SelectedPage = State()
    Category = State()
    MaxPage = State()
    ListProduct = State()
    Quantity = State()

class SupportFlow(StatesGroup):
    ListSupport = State()
    SelectSupport = State()


class InputUserQuantity(StatesGroup):
    waiting_quantity = State()

class ContactingSupport(StatesGroup):
    UserMessage = State()

class Payment(StatesGroup):
    PaymentID = State()
    Amount = State()

class Admin(StatesGroup):
    InputSQLCommand = State()
    SelectUser = State()
    ListUser = State()
    SelectSupport = State()
    ListSupport = State()
    IDDeleteTheProduct = State()
    AnswerAdminFromSupport = State()
    GetIDProduct = State()
    Choice = State()
    SelectOrder = State()
    ListOrder = State()

class AddProduct(StatesGroup):
    ProductName = State()
    ProductDescription = State()
    ProductPrice = State()
    ProductCategory = State()
    ProductPhoto = State()
