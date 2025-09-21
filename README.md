# 🛍️ ShopNaviTGBot

> Современный Telegram-бот для интернет-магазина с полным функционалом e-commerce

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-green.svg)](https://sqlalchemy.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.0+-red.svg)](https://aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Описание

ShopNaviTGBot - это полнофункциональный Telegram-бот для управления интернет-магазином. Бот предоставляет удобный интерфейс для покупателей и мощную панель администрирования для управления товарами, заказами и пользователями.

## ✨ Возможности

### Для пользователей:

- 🛒 **Корзина покупок** - добавление/удаление товаров, изменение количества
- 📱 **Каталог товаров** - просмотр товаров по категориям
- 🔍 **Поиск товаров** - быстрый поиск нужного товара
- 📦 **История заказов** - отслеживание статуса заказов
- 📍 **Управление адресами** - сохранение адресов доставки
- 💬 **Поддержка** - система обращений в техподдержку
- 👤 **Личный кабинет** - управление профилем пользователя

### Для администраторов:

- 📊 **Панель управления** - полная статистика магазина
- 🏷️ **Управление товарами** - добавление, редактирование, удаление
- 📂 **Категории** - создание и управление категориями товаров
- 📋 **Заказы** - просмотр и управление заказами
- 👥 **Пользователи** - управление базой пользователей
- 🎫 **Поддержка** - обработка обращений пользователей

## 🛠️ Технологический стек

- **Язык программирования:** Python 3.13+
- **Telegram API:** aiogram 3.21+
- **База данных:** PostgreSQL
- **ORM:** SQLAlchemy 2.0+ (Async)
- **Миграции:** Alembic 1.16+
- **Архитектура:** FSM (Finite State Machine)
- **Контейнеризация:** Docker & Docker Compose
- **Платежная система:** YooKassa 3.6+
- **HTTP клиент:** aiohttp 3.12+

## 📦 Установка и настройка

### Предварительные требования

- Python 3.9 или выше
- PostgreSQL (или SQLite для разработки)
- Docker и Docker Compose (для контейнеризированной установки)
- Git

### Вариант 1: Установка через Docker (Рекомендуется) 🐳

**Быстрый запуск с Docker Compose:**

1. **Клонирование репозитория**

   ```bash
   git clone https://github.com/yourusername/ShopNaviTGBot.git
   cd ShopNaviTGBot
   ```

2. **Настройка переменных окружения**

   Отредактируйте файл `.env`:

   ```env
   BOT_TOKEN=your_telegram_bot_token
   POSTGRES_DB=shopbot_db
   POSTGRES_USER=shopbot_user
   POSTGRES_PASSWORD=your_strong_password
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   ADMIN_IDS=123456789,987654321
   DEBUG=False
   ```

3. **Запуск всех сервисов**

   ```bash
   docker-compose up -d
   ```

4. **Применение миграций**
   ```bash
   docker-compose exec bot alembic upgrade head
   ```

**Готово! 🎉** Бот запущен и готов к работе.

### Вариант 2: Локальная установка

1. **Клонирование репозитория**

   ```bash
   git clone https://github.com/yourusername/ShopNaviTGBot.git
   cd ShopNaviTGBot
   ```

2. **Создание виртуального окружения**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate  # Windows
   ```

3. **Установка зависимостей**

   ```bash
   pip install -r requirements.txt
   ```

4. **Настройка переменных окружения**

   Создайте файл `.env` в корневой директории:

   ```env
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/shopbot_db
   ADMIN_IDS=123456789,987654321
   DEBUG=True
   ```

5. **Инициализация базы данных**

   ```bash
   python -m alembic upgrade head
   ```

6. **Запуск бота**
   ```bash
   python main.py
   ```

## 🐳 Docker команды

### Основные команды:

```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка всех сервисов
docker-compose down

# Просмотр логов
docker-compose logs -f bot

# Перезапуск только бота
docker-compose restart bot

# Выполнение команд внутри контейнера
docker-compose exec bot python manage.py some_command

# Применение миграций
docker-compose exec bot alembic upgrade head

# Создание новой миграции
docker-compose exec bot alembic revision --autogenerate -m "description"
```

### Разработка с Docker:

```bash
# Запуск в режиме разработки с hot-reload
docker-compose -f docker-compose.dev.yml up

# Подключение к базе данных
docker-compose exec postgres psql -U shopbot_user -d shopbot_db

# Просмотр статуса контейнеров
docker-compose ps
```

## 📁 Структура проекта

```
ShopNaviTGBot/
├── 📂 app/                    # Основная папка приложения
│   ├── config.py             # Конфигурация приложения
│   ├── states.py             # FSM состояния
│   ├── templates.py          # Шаблоны сообщений
│   ├── 📂 DB/                # База данных
│   │   ├── connection.py     # Подключение к БД
│   │   ├── table_data_base.py # SQLAlchemy модели
│   │   └── __init__.py
│   ├── 📂 Handlers/          # Обработчики команд и коллбэков
│   │   ├── about.py          # Информация о боте
│   │   ├── admin.py          # Административные функции
│   │   ├── basket.py         # Корзина покупок
│   │   ├── catalog.py        # Каталог товаров
│   │   ├── db_handlers.py    # Обработчики БД
│   │   ├── payment.py        # Платежная система
│   │   ├── registration.py   # Регистрация пользователей
│   │   ├── support.py        # Служба поддержки
│   │   ├── user.py           # Пользовательские функции
│   │   └── __init__.py
│   ├── 📂 keyboards/         # Клавиатуры для бота
│   │   ├── admin.py          # Админские клавиатуры
│   │   ├── basket.py         # Клавиатуры корзины
│   │   ├── catalog.py        # Клавиатуры каталога
│   │   ├── payment.py        # Клавиатуры оплаты
│   │   ├── registry.py       # Клавиатуры регистрации
│   │   ├── support.py        # Клавиатуры поддержки
│   │   ├── user.py           # Пользовательские клавиатуры
│   │   └── __init__.py
│   ├── 📂 migrations/        # Alembic миграции
│   │   ├── env.py            # Конфигурация Alembic
│   │   ├── script.py.mako    # Шаблон миграций
│   │   ├── 📂 versions/      # Файлы миграций
│   │   └── README
│   └── 📂 Tools/             # Вспомогательные инструменты
│       ├── catalog.py        # Утилиты каталога
│       └── different.py      # Разные утилиты
├── 📂 venv/                  # Виртуальное окружение
├── .dockerignore             # Docker ignore файл
├── .env                      # Переменные окружения
├── .gitignore               # Git ignore файл
├── alembic.ini              # Конфигурация Alembic
├── compose.yml              # Docker Compose конфигурация
├── Dockerfile               # Docker образ
├── main.py                  # Точка входа приложения
├── packages.txt             # Список пакетов
└── README.md                # Документация
```

## 🗄️ Схема базы данных

### Основные таблицы:

- **users** - Информация о пользователях
- **categories** - Категории товаров
- **products** - Товары магазина
- **orders** - Заказы пользователей
- **order_items** - Товары в заказах
- **cart_items** - Корзина покупок
- **admins** - Администраторы системы
- **support_messages** - Обращения в поддержку

## 🚀 Деплой в продакшен

### С использованием Docker:

1. **Клонирование на сервер**

   ```bash
   git clone https://github.com/yourusername/ShopNaviTGBot.git
   cd ShopNaviTGBot
   ```

2. **Настройка продакшен окружения**

   ```bash
   cp .env.example .env
   # Отредактируйте .env для продакшена
   ```

3. **Запуск в продакшене**

   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

4. **Настройка SSL (опционально)**
   ```bash
   # Используйте nginx-proxy или traefik для SSL
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 🚀 Использование

### Для пользователей:

1. Начните диалог с ботом командой `/start`
2. Изучите каталог товаров
3. Добавьте товары в корзину
4. Оформите заказ
5. Отслеживайте статус заказа

### Для администраторов:

1. Получите права администратора
2. В панели появится кнопка `Админа-панель`
3. Управляйте товарами, заказами и пользователями
4. Отвечайте на обращения в поддержку


## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Чтобы внести свой вклад:

1. Сделайте Fork репозитория
2. Создайте feature-ветку (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - смотрите файл [LICENSE](LICENSE) для подробностей.

## 📞 Поддержка

Если у вас есть вопросы или предложения:

- 📧 **Email:** support@shopnavibot.com
- 💬 **Telegram:** [@YourUsername](https://t.me/YourUsername)
- 🐛 **Issues:** [GitHub Issues](https://github.com/yourusername/ShopNaviTGBot/issues)



## 🔧 Мониторинг и логирование

### Просмотр логов в Docker:

```bash
# Логи бота
docker-compose logs -f bot

# Логи базы данных
docker-compose logs -f postgres

# Все логи
docker-compose logs -f
```

### Мониторинг ресурсов:

```bash
# Использование ресурсов контейнерами
docker stats

# Информация о контейнерах
docker-compose ps
```

---

<div align="center">

**[⬆ Наверх](#-shopnavitgbot)**

Сделано с ❤️ для развития e-commerce в Telegram

</div>
