from loguru import logger

from dal.user import User
from schemas import BaseExercise


class Reviews:
    @classmethod
    async def create_reviews(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS reviews(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER,
                    review TEXT
                    )
                    """)

    @classmethod
    async def add_review(cls, user_id, review):
        await cur.execute(f"""
        INSERT INTO reviews
        (user_id, review)
        VALUES
        ({user_id}, '{review}')
        """)

        logger.info(f'Отзыв от пользователя с id = {user_id} был добавлен')
