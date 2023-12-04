import pathlib

from loguru import logger
import aiosqlite as sq

import schemas

boolean_dict = {True: 1, False: 0}


class User:
    @classmethod
    async def db_start(cls):
        global db, cur
        db = await sq.connect(str(pathlib.Path(__file__).parent.parent) + '/tg.db', isolation_level=None)
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
                    times_per_week INTEGER,
                    
                    rebuilt BOOLEAN DEFAULT 0 CHECK (rebuilt IN (0, 1)),
                    subscribed BOOLEAN DEFAULT 0 CHECK (subscribed IN (0, 1)),
                    first_training BOOLEAN DEFAULT 1 CHECK (first_training IN (0, 1))
                    )
                    """)

    @classmethod
    async def get_db_cur(cls):
        return db, cur

    @classmethod
    async def add_attributes(cls, state, user_id, chat_id):
        user = await cls.select_attributes(user_id)
        async with state.proxy() as data:
            if user:
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
                    chat_id = {chat_id}
                    
                    WHERE tg_id = '{user_id}'
                """)
                await db.commit()
            else:
                query = f"""
                    INSERT INTO users
                    (
                    tg_id,
                    chat_id,
                    gender,
                    age,
                    height,
                    weight,
                    gym_experience,
                    
                    squats_results,
                    bench_results,
                    deadlift_results,
                    
                    goals,
                    intensity,
                    health_restrictions,
                    times_per_week
                    
                    )
                    VALUES
                    (
                    {user_id},
                    {chat_id},
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
                    '{data['times_per_week']}'
                    )
                """
                await cur.execute(query)
                await db.commit()
            return True

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
    async def update_rebuilt_parameter(cls, user_id):
        await cur.execute(f"""
                UPDATE users
                SET rebuilt = 1
                WHERE tg_id = {user_id}
            """)
        logger.info(f'Параметр rebuilt у пользователя с id = {user_id} изменен на 1')

        await db.commit()

    @classmethod
    async def update_subscribed_parameter(cls, user_id, value):
        await cur.execute(f"""
                    UPDATE users
                    SET subscribed = {value}
                    WHERE tg_id = {user_id}
                """)
        logger.info(f'Параметр subscribed у пользователя с id = {user_id} изменен на {value}')

        await db.commit()

    @classmethod
    async def update_first_training_parameter(cls, user_id):
        await cur.execute(f"""
                        UPDATE users
                        SET first_training = 0
                        WHERE tg_id = {user_id}
                    """)
        logger.info(f'Параметр first_training у пользователя с id = {user_id} изменен на 0')

        await db.commit()

    @classmethod
    async def update_chat_id_parameter(cls, user_id, chat_id):
        await cur.execute(f"""
            UPDATE users
            SET chat_id = {chat_id}
            WHERE tg_id = {user_id}
        """)

        await db.commit()

    @classmethod
    async def check_if_subscribed_by_user_id(cls, user_id):
        await cur.execute(f"""
                SELECT subscribed
                FROM users
                WHERE tg_id = {user_id}
            """)
        subscribed = await cur.fetchone()

        if subscribed[0]:
            logger.debug(f'Пользователь {user_id} подписан')
            return True
        else:
            logger.warning(f'Пользователь {user_id} не подписан')
            return False

    @classmethod
    async def check_if_rebuilt_by_user_id(cls, user_id):
        await cur.execute(f"""
                    SELECT rebuilt
                    FROM users
                    WHERE tg_id = {user_id}
                """)
        subscribed = await cur.fetchone()
        if subscribed[0]:
            logger.warning(f'Пользователь {user_id} уже пересобирал тренировку')
            return True
        else:
            logger.debug(f'Пользователь {user_id} еще не пересобирал тренировку')
            return False

    @classmethod
    async def check_if_first_training_by_user_id(cls, user_id):
        await cur.execute(f"""
            SELECT first_training
            FROM users
            WHERE tg_id = {user_id}
            """)
        first_training = await cur.fetchone()

        if first_training[0]:
            return True
        else:
            return False
