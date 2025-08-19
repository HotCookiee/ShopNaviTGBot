from aiogram.types import BotCommand

commands = [
    BotCommand(command="start",description="Start the bot"),
    BotCommand(command="help",description="Show help"),
    BotCommand(command="catalog", description="🛒 Каталог товаров"),
    BotCommand(command="cart", description="🧺 Моя корзина"),
    BotCommand(command="checkout", description="✅ Оформление заказа"),
    BotCommand(command="support", description="💬 Поддержка"),
    BotCommand(command="about", description="ℹ️ О нас"),
    BotCommand(command="profile", description="👤 Мой профиль"),
    BotCommand(command="exit", description="🚪 Выход"),
]