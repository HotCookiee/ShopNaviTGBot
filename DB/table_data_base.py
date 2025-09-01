from datetime import date

from sqlalchemy import String, Date, Text, LargeBinary, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship
from sqlalchemy.sql.schema import ForeignKey

__BASE = declarative_base()


# region Table User

class User(__BASE):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    number: Mapped[str] = mapped_column(String(30), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=True)
    vip_status: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(default="Пользователь", nullable=False)
    delivery_address: Mapped[str] = mapped_column(default="Не указано")
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(50), default="Не указано")
    date_registory: Mapped[date] = mapped_column(Date, default=date.today)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    cart_items: Mapped[list["CartItems"]] = relationship(back_populates="user")
    admins: Mapped["Admin"] = relationship(back_populates="user")
    notifications: Mapped["Notification"] = relationship(back_populates="user")
    support_message: Mapped["SupportMessage"] = relationship(back_populates="user")


class Category(__BASE):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(150), nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(__BASE):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(150), nullable=True)
    price: Mapped[int] = mapped_column(nullable=False)
    photo: Mapped[str] = mapped_column(String(), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    cart_items: Mapped["CartItems"] = relationship(back_populates="product")
    order_items: Mapped["OrderItems"] = relationship(back_populates="product")


class Order(__BASE):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False , default="Подготовка")
    delivery_address: Mapped[str] = mapped_column(default="Не указано")
    total_amount: Mapped[str] = mapped_column(String(150), nullable=False)

    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[list["OrderItems"]] = relationship(back_populates="order")


class CartItems(__BASE):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")


class OrderItems(__BASE):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)

    product: Mapped["Product"] = relationship(back_populates="order_items")
    order: Mapped["Order"] = relationship(back_populates="order_items")


# endregion

# region Admin Table

class Admin(__BASE):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=True)
    name: Mapped[str] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="admins")


class SupportMessage(__BASE):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    user_requests: Mapped[str] = mapped_column(String(1000), nullable=False)
    date_the_request_was_created: Mapped[date] = mapped_column(Date, default=date.today, nullable=True)
    admin_id: Mapped[int] = mapped_column(nullable=True)
    time_answer: Mapped[date] = mapped_column(Date, nullable=True)
    admin_answer: Mapped[str] = mapped_column(String(), nullable=True)
    application_status: Mapped[str] = mapped_column(String(50), nullable=True, default='В обработке')
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="support_message")



class Notification(__BASE):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    text: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="notifications")




# endregion
