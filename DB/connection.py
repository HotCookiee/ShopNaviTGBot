from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import POSTGRES_CONFIG

class Database:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.engine = create_async_engine(POSTGRES_CONFIG)
            cls.__instance.session_factory = async_sessionmaker(bind=cls.__instance.engine)
        return cls.__instance

    def __del__(self):
        __instance = None

    pass

    def get_session(self):
        return self.__instance.session_factory()
