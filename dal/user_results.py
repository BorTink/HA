from loguru import logger

from dal.user import User


class UserResults:
    @classmethod
    async def create_user_results(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_results(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER,
                    exercise_name INT,
                    weight INT
                    )
                    """)

    @classmethod
    async def update_user_results(cls, user_id, name, weight):
        await cur.execute(f"""
        SELECT user_results.id
        FROM user_results
        WHERE user_id = {user_id}
        AND exercise_name = '{name}'
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Результаты пользователя {user_id} для упражнения {name} были найдены,'
                         f' происходит обновление результатов')
            await cur.execute(f"""
                    UPDATE user_results
                    SET
                    (
                    exercise_name, weight
                    )
                    =
                    (
                    '{name}', {weight}
                    )
                    FROM exercises e 
                    WHERE user_id = {user_id}
                    AND exercise_name = '{name}'
                    """)
            logger.info(f'Результаты пользователя {user_id} для упражнения {name} были обновлены')

        else:
            logger.debug(f'Результаты пользователя {user_id} для упражнения {name} не были найдены,'
                         f' вносятся новые результаты.')
            await cur.execute(f"""
                    INSERT INTO user_results
                    (
                    user_id, exercise_name, weight
                    )
                    VALUES
                    (
                    {user_id}, '{name}', {weight}
                    )
                    """)
            logger.info(f'Результаты пользователя с id = {user_id} для упражнения {name} были внесены.')

        await db.commit()

    @classmethod
    async def get_user_results_by_day_of_week(cls, user_id, day_of_week):
        await cur.execute(f"""
            SELECT weight
            FROM user_results
            WHERE user_id = {user_id}
            AND day_of_week = '{day_of_week}'
            """)
        user_results = await cur.fetchone()
        if not user_results:
            return None

        user_results = dict(user_results)
        return user_results
