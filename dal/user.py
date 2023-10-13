from loguru import logger
import aiosqlite as sq

import schemas


class User:
    @classmethod
    async def db_start(cls):
        global db, cur
        db = await sq.connect('tg.db')
        db.row_factory = sq.Row
        cur = await db.cursor()

        logger.info(cur)
        logger.info(type(cur))

        await cur.execute(""" 
                    CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    tg_id INTEGER, 
                    gender TEXT,
                    age TEXT,
                    height TEXT,
                    weight TEXT,
                    gym_experience TEXT,
                    goal TEXT,
                    time_to_reach INTEGER,
                    intensity TEXT,
                    times_per_week INTEGER,
                    health_restrictions TEXT,
                    squats_results TEXT,
                    bench_results TEXT,
                    deadlift_results TEXT
                    )
                    """)

    @classmethod
    async def get_db_cur(cls):
        return db, cur

    @classmethod
    async def add_attributes(cls, state, user_id):
        user = await cls.select_attributes(user_id)
        async with state.proxy() as data:
            if user:
                if user.attempts >= 2:
                    logger.error(f'Превышено кол-во попыток на пересоздание расписания')
                    return False
                await cur.execute(f"""
                    UPDATE users
                    SET
                    gender = '{data['gender']}',
                    age = '{data['age']}',
                    height = '{data['height']}',
                    weight = '{data['weight']}',
                    gym_experience = '{data['gym_experience']}',
                    goal = '{data['goal']}',
                    time_to_reach = '{data['time_to_reach']}',
                    intensity = '{data['intensity']}',
                    times_per_week = '{data['times_per_week']}',
                    health_restrictions = '{data['health_restrictions']}',
                    squats_results = '{data['squats_results']}',
                    bench_results = '{data['bench_results']}',
                    deadlift_results = '{data['deadlift_results']}'
                    WHERE tg_id = '{user_id}'
                """)
                await db.commit()
            else:
                query = f"""
                    INSERT INTO users
                    (
                    tg_id,
                    gender,
                    age,
                    height,
                    weight,
                    gym_experience,
                    goal,
                    time_to_reach,
                    intensity,
                    times_per_week,
                    health_restrictions,
                    squats_results,
                    bench_results,
                    deadlift_results
                    )
                    VALUES
                    (
                    {user_id},
                    '{data['gender']}',
                    '{data['age']}',
                    '{data['height']}',
                    '{data['weight']}',
                    '{data['gym_experience']}',
                    '{data['goal']}',
                    '{data['time_to_reach']}',
                    '{data['intensity']}',
                    '{data['times_per_week']},
                    '{data['health_restrictions']}',
                    '{data['squats_results']}',
                    '{data['bench_results']}',
                    '{data['deadlift_results']}'
                    )
                """
                await cur.execute(query)
                await db.commit()
            return True

    @classmethod
    async def get_user(cls, user_id):
        await cur.execute(f"""
                    SELECT *
                    FROM users
                    WHERE tg_id = {user_id}
                """)
        user_info = await cur.fetchone()
        if user_info is None:
            logger.debug(f'Пользователя с id = {user_id} не существует')
            return None
        else:
            return user_info

    @classmethod
    async def select_attributes(cls, user_id):
        await cur.execute(f"""
                SELECT *
                FROM users
                WHERE tg_id = {user_id}
            """)
        user_info = await cur.fetchone()
        if user_info is None:
            logger.debug(f'Пользователя с id = {user_id} не существует')
            return None

        user_info = schemas.PromptData(**dict(user_info))
        return user_info

    @classmethod
    async def increase_attempts_by_user_id(cls, user_id):
        try:
            await cur.execute(f"""
                UPDATE users
                SET attempts = attempts + 1
                WHERE tg_id = {user_id}
                RETURNING attempts
            """)
            attempts = await cur.fetchone()
            if attempts is None:
                logger.error(f'Попытки у пользователя с id = {user_id} не найдены')
                raise Exception
            logger.info(f'Количество попыток у пользователя с id = {user_id} увеличено до {attempts}')
            await db.commit()

        except Exception as exc:
            logger.error(f'При увеличении количества попыток у пользователя с id = {user_id} произошла ошибка: {exc}')
            raise Exception

