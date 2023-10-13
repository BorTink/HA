from loguru import logger

from dal.user import User


class Exercises:
    @classmethod
    async def create_exercises(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS exercises(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT,
                    link TEXT
                    )
                    """)

    @classmethod
    async def get_exercise_link(cls, name):
        await cur.execute(f"""
        SELECT link
        FROM exercises
        WHERE name = {name}
        """)
        exercise_link = await cur.fetchone()

        if exercise_link:
            logger.debug(f'Инструкция к тренировке {name} была найдена - {exercise_link}')
            return exercise_link
        else:
            logger.debug(f'Инструкция к тренировке {name} не была найдена. Производится поиск инструкции')
            return None  # TODO: Интегрировать YouTube Search API для поиска инструкций
