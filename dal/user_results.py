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
                    exercise_id INT,
                    sets INT,
                    weight INT,
                    reps INT,
                    time INT
                    )
                    """)

    @classmethod
    async def update_user_results(cls, user_id, name, sets, weight, reps, time):
        await cur.execute(f"""
        SELECT id
        FROM user_results
        JOIN exercises ON exercises.name = '{name}'
        WHERE user_id = {user_id}
        AND exercise_id = exercises.id
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Результаты пользователя {user_id} для упражнения {name} были найдены,'
                         f' происходит обновление результатов')
            await cur.execute(f"""
                    UPDATE user_results
                    SET
                    (
                    sets, weight, reps, time
                    )
                    =
                    (
                    {sets}, {weight}, {reps}, {time}
                    )
                    WHERE user_id = {user_id}
                    AND exercise_id = exercises.id
                    """)
            logger.info(f'Результаты пользователя {user_id} для упражнения {name} были обновлены')

        else:
            logger.debug(f'Результаты пользователя {user_id} для упражнения {name} не были найдены,'
                         f' вносятся новые результаты.')
            await cur.execute(f"""
                    INSERT INTO user_results
                    (
                    user_id, sets, weight, reps, time
                    )
                    VALUES
                    (
                    {user_id}, {sets}, {weight}, {reps}, {time}
                    )
                    """)
            logger.info(f'Результаты пользователя с id = {user_id} для упражнения {name} были внесены.')

        await db.commit()

    @classmethod
    async def get_user_results_by_day_of_week(cls, user_id, day_of_week):
        await cur.execute(f"""
            SELECT sets, weight, reps, time
            FROM user_results
            WHERE user_id = {user_id}
            AND day_of_week = '{day_of_week}'
            """)
        user_results = await cur.fetchone()
        user_results = dict(user_results)
        if not user_results:
            return None

        if user_results['time'] is None:
            user_results.pop('time')
        else:
            user_results.pop('sets')
            user_results.pop('weight')
            user_results.pop('reps')
        return user_results
