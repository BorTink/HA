from loguru import logger
import sqlite3 as sq

import schemas


class User:
    @classmethod
    async def db_start(cls):
        global db, cur
        db = sq.connect('tg.db')
        db.row_factory = sq.Row
        cur = db.cursor()
        cur.execute(""" 
                    CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    tg_id TEXT, 
                    sex TEXT,
                    age TEXT,
                    height TEXT,
                    weight TEXT,
                    illnesses TEXT,
                    drugs TEXT,
                    level_of_fitness TEXT,
                    goal TEXT,
                    result TEXT,
                    allergy TEXT,
                    diet TEXT,
                    number_of_meals TEXT,
                    trainings_per_week TEXT,
                    train_time_amount TEXT,
                    gym_access TEXT,
                    gym_equipment TEXT
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
                cur.execute(f"""
                    UPDATE users
                    SET
                    sex = '{data['sex']}',
                    age = '{data['age']}',
                    height = '{data['height']}',
                    weight = '{data['weight']}',
                    illnesses = '{data['illnesses']}',
                    drugs = '{data['drugs']}',
                    level_of_fitness = '{data['level_of_fitness']}',
                    goal = '{data['goal']}',
                    result = '{data['result']}',
                    allergy = '{data['allergy']}',
                    diet = '{data['diet']}',
                    number_of_meals = '{data['number_of_meals']}',
                    trainings_per_week = '{data['trainings_per_week']}',
                    train_time_amount = '{data['train_time_amount']}',
                    gym_access = '{data['gym_access']}',
                    gym_equipment = '{data['gym_equipment']}'
                    WHERE tg_id = '{user_id}'
                """)
                db.commit()
            else:
                query = f"""
                    INSERT INTO users
                    (
                    tg_id,
                    sex,
                    age,
                    height,
                    weight,
                    illnesses,
                    drugs,
                    level_of_fitness,
                    goal,
                    result,
                    allergy,
                    diet,
                    number_of_meals,
                    trainings_per_week,
                    train_time_amount,
                    gym_access,
                    gym_equipment
                    )
                    VALUES
                    (
                    {user_id},
                    '{data['sex']}',
                    '{data['age']}',
                    '{data['height']}',
                    '{data['weight']}',
                    '{data['illnesses']}',
                    '{data['drugs']}',
                    '{data['level_of_fitness']}',
                    '{data['goal']}',
                    '{data['result']}',
                    '{data['allergy']}',
                    '{data['diet']}',
                    '{data['number_of_meals']}',
                    '{data['trainings_per_week']}',
                    '{data['train_time_amount']}',
                    '{data['gym_access']}',
                    '{data['gym_equipment']}'
                    )
                """
                cur.execute(query)
                db.commit()

    @classmethod
    async def get_user(cls, user_id):
        cur.execute(f"""
                    SELECT *
                    FROM users
                    WHERE tg_id = {user_id}
                """)
        user_info = cur.fetchone()
        if user_info is None:
            logger.debug(f'Пользователя с id = {user_id} не существует')
            return None
        else:
            return user_info

    @classmethod
    async def select_attributes(cls, user_id):
        cur.execute(f"""
                SELECT 
                    sex,
                    age,
                    height,
                    weight,
                    illnesses,
                    drugs,
                    level_of_fitness,
                    goal,
                    result,
                    allergy,
                    diet,
                    number_of_meals,
                    trainings_per_week,
                    train_time_amount,
                    gym_access,
                    gym_equipment
                FROM users
                WHERE tg_id = {user_id}
            """)
        user_info = cur.fetchone()
        if user_info is None:
            logger.debug(f'Пользователя с id = {user_id} не существует')
            return None

        user_info = schemas.PromptData(**dict(user_info))
        return user_info
