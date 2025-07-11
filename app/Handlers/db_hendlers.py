from DB.table_data_base import Testing
from DB.connection import Database

db = Database()

async def add_user():
    async with db.get_session() as session:
        new_user = Testing (
            name="GErw",
            age=213,
        )
        session.add(new_user)
        await session.commit()
