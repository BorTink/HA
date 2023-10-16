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
                    age INTEGER,
                    height INTEGER,
                    weight INTEGER,
                    gym_experience TEXT,
                    
                    bench_results INTEGER,
                    deadlift_results INTEGER,
                    squats_results INTEGER,
                    
                    goals TEXT,
                    intensity TEXT,
                    health_restrictions TEXT,
                    times_per_week INTEGER
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
                    
                    squats_results = '{data['squats_results']}',
                    bench_results = '{data['bench_results']}',
                    deadlift_results = '{data['deadlift_results']}',
                    
                    goals = '{data['goals']}',
                    intensity = '{data['intensity']}',
                    health_restrictions = '{data['health_restrictions']}',
                    times_per_week = '{data['times_per_week']}'
                    
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
                    
                    squats_results,
                    bench_results,
                    deadlift_results
                    
                    goals,
                    intensity,
                    health_restrictions,
                    times_per_week,
                    
                    )
                    VALUES
                    (
                    {user_id},
                    '{data['gender']}',
                    '{data['age']}',
                    '{data['height']}',
                    '{data['weight']}',
                    '{data['gym_experience']}',
                    
                    '{data['squats_results']}',
                    '{data['bench_results']}',
                    '{data['deadlift_results']}',
                    
                    '{data['goals']}',
                    '{data['intensity']}',
                    '{data['health_restrictions']}',
                    '{data['times_per_week']}
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
