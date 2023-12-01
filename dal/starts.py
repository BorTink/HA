from loguru import logger

from dal.user import User
from schemas import BaseExercise


class Starts:
    @classmethod
    async def create_starts(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS starts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER,
                    clicks INTEGER,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)

    @classmethod
    async def update_starts(cls, user_id):
        await cur.execute(
            f"""
            SELECT id
            FROM starts
            WHERE user_id = {user_id}
            """
        )
        user = await cur.fetchone()

        if user:
            await cur.execute(
                f"""
                UPDATE starts
                SET clicks = clicks + 1
                WHERE user_id = {user_id}
                """
            )
        else:
            await cur.execute(
                f"""
                INSERT INTO starts (user_id, clicks)
                VALUES ({user_id}, 1)
                """
            )
        await db.commit()
