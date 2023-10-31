from loguru import logger

from dal.user import User


class Trainings:
    @classmethod
    async def create_trainings(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS trainings(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER,
                    day INTEGER,
                    data TEXT,
                    is_rest BOOLEAN
                    )
                    """)

    @classmethod
    async def remove_prev_trainings(cls, user_id):
        await cur.execute(f"""
        DELETE FROM trainings
        WHERE user_id = {user_id}
        """)

        logger.info(f'Все тренировки пользователя с id = {user_id} были удалены.')
        await db.commit()

    @classmethod
    async def update_trainings(cls, user_id, day, data, is_rest):
        await cur.execute(f"""
        SELECT id
        FROM trainings
        WHERE user_id = {user_id}
        AND day = '{day}'
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Тренировки пользователя {user_id} на день {day} были найдены,'
                         f' происходит обновление тренировок')
            await cur.execute(f"""
                    UPDATE trainings
                    SET
                    (
                    user_id, day, data, is_rest
                    )
                    =
                    (
                    {user_id}, '{day}', '{data}', {is_rest}
                    )
                    WHERE user_id = {user_id}
                    AND day = '{day}'
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были обновлены.')

        else:
            logger.debug(f'Тренировки пользователя с id = {user_id} на день {day} не были найдены,'
                         f' создаются новые тренировки.')
            await cur.execute(f"""
                    INSERT INTO trainings
                    (
                    user_id, day, data, is_rest
                    )
                    VALUES
                    (
                    {user_id}, '{day}', '{data}', {is_rest}
                    )
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были созданы.')

        await db.commit()

    @classmethod
    async def get_trainings_by_day(cls, user_id, day):
        await cur.execute(f"""
            SELECT data, day
            FROM trainings
            WHERE user_id = {user_id}
            AND day = '{day}'
            """)
        trainings = await cur.fetchone()

        return trainings if trainings else (None, None)

    @classmethod
    async def get_next_training(cls, user_id, current_day):
        await cur.execute(f"""
                SELECT data, day
                FROM trainings
                WHERE user_id = {user_id}
                AND day > {current_day}
                ORDER BY day ASC
                """)
        trainings = await cur.fetchone()

        return trainings if trainings else (None, None)

    @classmethod
    async def get_prev_training(cls, user_id, current_day):
        await cur.execute(f"""
                SELECT data, day
                FROM trainings
                WHERE user_id = {user_id}
                AND day < {current_day}
                ORDER BY day DESC
                """)
        trainings = await cur.fetchone()

        return trainings if trainings else (None, None)
