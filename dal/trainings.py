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
                    user_id INT,
                    day_of_week TEXT,
                    iteration INT,
                    data TEXT,
                    goal_time_period INT DEFAULT 10
                    )
                    """)

    @classmethod
    async def update_trainings(cls, user_id, day_of_week, iteration, data, goal_time_period):
        await cur.execute(f"""
        SELECT id
        FROM trainings
        WHERE user_id = {user_id}
        AND day_of_week = '{day_of_week}'
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Тренировки пользователя {user_id} на {day_of_week} были найдены,'
                         f' происходит обновление тренировок')
            await cur.execute(f"""
                    UPDATE trainings
                    SET
                    (
                    user_id, day_of_week, iteration, data, goal_time_period
                    )
                    =
                    (
                    {user_id}, '{day_of_week}', {iteration}, '{data}', {goal_time_period}
                    )
                    WHERE user_id = {user_id}
                    AND day_of_week = '{day_of_week}'
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были обновлены.')

        else:
            logger.debug(f'Тренировки пользователя с id = {user_id} на {day_of_week} не были найдены,'
                         f' создаются новые тренировки.')
            await cur.execute(f"""
                    INSERT INTO trainings
                    (
                    user_id, day_of_week, iteration, data, goal_time_period
                    )
                    VALUES
                    (
                    {user_id}, '{day_of_week}', {iteration}, '{data}', {goal_time_period}
                    )
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были созданы.')

        await db.commit()

    @classmethod
    async def get_trainings_by_day_of_week(cls, user_id, day_of_week):
        await cur.execute(f"""
            SELECT data
            FROM trainings
            WHERE user_id = {user_id}
            AND day_of_week = '{day_of_week}'
            """)
        trainings = await cur.fetchone()

        return trainings if trainings else None
