from loguru import logger

import schemas
from dal.user import User
from schemas import BaseExercise


class Meals:
    @classmethod
    async def create_meals(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS meals(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER,
                    day INTEGER,
                    meal_plan TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)

    @classmethod
    async def insert_meal(cls, user_id, day, meal_plan):
        await cur.execute(
            f"""
            INSERT INTO meals (user_id, day, meal_plan)
            VALUES ({user_id}, {day}, '{meal_plan}')
            """
        )
        await db.commit()

    @classmethod
    async def get_meal_by_day(cls, user_id, day):
        await cur.execute(f"""
            SELECT meal_plan, day
            FROM meals
            WHERE user_id = {user_id}
            AND day = {day}
            """)
        meal = await cur.fetchone()

        return meal if meal else (None, None)

    @classmethod
    async def get_all_meals_by_user_id(cls, user_id):
        await cur.execute(f"""
            SELECT meal_plan, day
            FROM meals
            WHERE user_id = {user_id}
            """)
        meals = await cur.fetchall()

        return [schemas.Meal(**dict(meal)) for meal in meals] if meals else None
