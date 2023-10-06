from loguru import logger
import sqlite3 as sq

from dal.user import User
import schemas


class ShoppingList:
    @classmethod
    async def create_shopping_list(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS shopping_list(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    tg_id TEXT,
                    shopping_list_data TEXT
                    )
                    """)

    @classmethod
    async def update_shopping_list(cls, user_id, shopping_list_data):
        await cur.execute(f"""
        SELECT id
        FROM shopping_list
        WHERE tg_id = {user_id}
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Список продуктов для покупки пользователя {user_id} был найден, '
                         f'происходит обновление списка')
            await cur.execute(f"""
                    UPDATE shopping_list
                    SET
                    (tg_id, shopping_list_data)
                    =
                    ({user_id}, '{shopping_list_data}')
                    """)
            logger.info(f'Список продуктов для покупки пользователя с id = {user_id} был обновлен.')

        else:
            logger.debug(f'Список продуктов для покупки пользователя с id = {user_id} не был найден,'
                         f' создается новый список.')
            await cur.execute(f"""
                    INSERT INTO shopping_list
                    (tg_id, shopping_list_data)
                    VALUES
                    ({user_id}, '{shopping_list_data}')
                    """)
            logger.info(f'Список продуктов для покупки пользователя с id = {user_id} был создан.')

        await db.commit()

    @classmethod
    async def get_shopping_list(cls, user_id):
        await cur.execute(f"""
            SELECT tg_id, shopping_list_data
            FROM shopping_list
            WHERE tg_id = {user_id}
            """)
        shopping_list = await cur.fetchone()
        if shopping_list:
            return dict(shopping_list)['shopping_list_data']
        else:
            return None
