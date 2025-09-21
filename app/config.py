import os

from dotenv import load_dotenv

load_dotenv()

TOKEN_CONF       = os.getenv("TOKEN")
PAY_API_KEY_CONF = os.getenv("PAY_API_KEY")
SHOP_ID_CONF     = os.getenv("SHOP_ID")
SECRET_KEY_CONF  = os.getenv("SECRET_KEY")
POSTGRES_CONFIG  = f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("HOST")}:{os.getenv("PORT",default="5432")}/{os.getenv("NAME_DB")}'



