from loguru import logger

from dal.user import User
from schemas import BaseExercise


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

    @classmethod
    async def get_all_similar_exercises_by_word(cls, word):
        await cur.execute(f"""
        SELECT title as name, url as link
        FROM website_exercises
        WHERE name LIKE '%{word}%'
        """) # TODO: Вернуть на name, link
        similar_exercises = await cur.fetchall()

        if similar_exercises:
            logger.debug(f'Было найдено {len(similar_exercises)} упражнений по слову {word}')
            return [BaseExercise(**res) for res in similar_exercises]
        else:
            logger.debug(f'Было найдено 0 упражнений по слову {word}')
            return 0

    @classmethod
    async def add_exercise(cls, name):
        await cur.execute(f"""
        SELECT link
        FROM exercises
        WHERE name = '{name}'
        """)
        exercise_link = await cur.fetchone()

        if exercise_link:
            logger.info(f'Упражнение {name} было уже вписано')
        else:
            logger.info(f'Упражнение {name} было не найдено, добавляем название')
            await cur.execute(f"""
                    INSERT INTO exercises
                    (name)
                    VALUES
                    ('{name}')
                    RETURNING link
            """)
            logger.info(f'Упражнение {name} было добавлено)')
            # TODO: Интегрировать YouTube Search API для поиска инструкций
