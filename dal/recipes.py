from loguru import logger
import sqlite3 as sq

from dal.user import User
import schemas


class Recipes:
    @classmethod
    async def create_recipes(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS recipes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    tg_id TEXT,
                    day_of_week TEXT,
                    recipes_data TEXT
                    )
                    """)

    @classmethod
    async def update_recipes(cls, user_id, day_of_week, recipes_data):
        cur.execute(f"""
        SELECT id
        FROM recipes
        WHERE tg_id = {user_id}
        AND day_of_week = '{day_of_week}'
        """)
        user = cur.fetchone()

        if user:
            logger.debug(f'Рецепты пользователя {user_id} на {day_of_week} были найдены,'
                         f' происходит обновление рецептов')
            cur.execute(f"""
                    UPDATE recipes
                    SET
                    (tg_id, day_of_week, recipes_data)
                    =
                    ({user_id}, '{day_of_week}', '{recipes_data}')
                    WHERE tg_id = {user_id}
                    AND day_of_week = '{day_of_week}'
                    """)
            logger.info(f'Рецепты пользователя с id = {user_id} были обновлены.')

        else:
            logger.debug(f'Рецепты пользователя с id = {user_id} на {day_of_week} не были найдены,'
                         f' создаются новые рецепты.')
            cur.execute(f"""
                    INSERT INTO recipes
                    (tg_id, day_of_week, recipes_data)
                    VALUES
                    ({user_id}, '{day_of_week}', '{recipes_data}')
                    """)
            logger.info(f'Рецепты пользователя с id = {user_id} были созданы.')

        db.commit()

    @classmethod
    async def get_recipes_by_day_of_week(cls, user_id, day_of_week):
        cur.execute(f"""
            SELECT tg_id, day_of_week, recipes_data
            FROM recipes
            WHERE tg_id = {user_id}
            AND day_of_week = '{day_of_week}'
            """)
        recipes = cur.fetchone()
        if recipes:
            return dict(recipes)['recipes_data']
        else:
            return None
