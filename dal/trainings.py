from loguru import logger
import sqlite3 as sq

from dal.user import User
import schemas


class Trainings:
    @classmethod
    async def create_trainings(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS trainings(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    tg_id TEXT,
                    day_of_week TEXT,
                    trainings_data TEXT
                    )
                    """)

    @classmethod
    async def update_trainings(cls, user_id, day_of_week, trainings_data):
        cur.execute(f"""
        SELECT id
        FROM trainings
        WHERE tg_id = {user_id}
        """)
        user = cur.fetchone()

        if user:
            logger.debug(f'Тренировки пользователя {user_id} были найдены, происходит обновление тренировок')
            cur.execute(f"""
                    UPDATE trainings
                    SET
                    (tg_id, day_of_week, trainings_data)
                    =
                    ({user_id}, '{day_of_week}', '{trainings_data}')
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были обновлены.')

        else:
            logger.debug(f'Тренировки пользователя с id = {user_id} не были найдены,'
                         f' создаются новые тренировки.')
            cur.execute(f"""
                    INSERT INTO trainings
                    (tg_id, day_of_week, trainings_data)
                    VALUES
                    ({user_id}, '{day_of_week}', '{trainings_data}')
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были созданы.')

        db.commit()

    @classmethod
    async def get_trainings_by_day_of_week(cls, user_id, day_of_week):
        cur.execute(f"""
            SELECT tg_id, day_of_week, trainings_data
            FROM trainings
            WHERE tg_id = {user_id}
            AND day_of_week = '{day_of_week}'
            """)
        trainings = cur.fetchone()
        if trainings:
            return dict(trainings)['trainings_data']
        else:
            return None
