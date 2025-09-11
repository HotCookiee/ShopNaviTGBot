from ..DB.connection import Database

db = Database()


async def add_data_to_the_table(name_table, **kwargs):
    async with db.get_session() as session:
        new_entry = name_table(**kwargs)
        session.add(new_entry)
        await session.commit()


async def completing_the_task(command):
    try:
        async with db.get_session() as session:
            async with session.begin():
                await session.execute(command)
    except Exception as e:
        print(e)
