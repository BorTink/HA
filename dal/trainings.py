from loguru import logger

from dal.user import User
from schemas import ReminderTraining

boolean_dict = {True: 1, False: 0}


class Trainings:
    @classmethod
    async def create_trainings(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS trainings(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER,
                    day INTEGER,
                    data TEXT,
                    active BOOLEAN DEFAULT 0 CHECK (active IN (0, 1)),
                    in_progress BOOLEAN DEFAULT 0 CHECK (in_progress IN (0, 1)),
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)

    @classmethod
    async def remove_prev_trainings(cls, user_id):
        await cur.execute(f"""
        DELETE FROM trainings
        WHERE user_id = {user_id}
        """)

        logger.info(f'Все тренировки пользователя с id = {user_id} были удалены.')
        await db.commit()

    @classmethod
    async def update_trainings(cls, user_id, day, data, active=False, in_progress=False):
        active = boolean_dict[active]
        in_progress = boolean_dict[in_progress]

        await cur.execute(f"""
        SELECT id
        FROM trainings
        WHERE user_id = {user_id}
        AND day = {day}
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Тренировки пользователя {user_id} на день {day} были найдены,'
                         f' происходит обновление тренировок')
            await cur.execute(f"""
                    UPDATE trainings
                    SET
                    (
                    user_id, day, data, active, in_progress
                    )
                    =
                    (
                    {user_id}, {day}, '{data}', {active}, {in_progress}
                    )
                    WHERE user_id = {user_id}
                    AND day = {day}
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были обновлены.')

        else:
            logger.debug(f'Тренировки пользователя с id = {user_id} на день {day} не были найдены,'
                         f' создаются новые тренировки.')
            await cur.execute(f"""
                    INSERT INTO trainings
                    (
                    user_id, day, data, active, in_progress
                    )
                    VALUES
                    (
                    {user_id}, {day}, '{data}', {active}, {in_progress}
                    )
                    """)
            logger.info(f'Тренировки пользователя с id = {user_id} были созданы.')

        await db.commit()

    @classmethod
    async def update_active_training_by_day(cls, user_id, day, active):
        active = boolean_dict[active]

        await cur.execute(f"""
                            UPDATE trainings
                            SET
                            active = {active}
                            WHERE user_id = {user_id}
                            AND day = {day}
                            RETURNING id
                            """)
        get_id = await cur.fetchone()
        if get_id:
            logger.info(f'Параметр active на тренировке дня {day} у пользователя с id = {user_id} '
                        f'был обновлен на {active}.')
        else:
            logger.error(f'Не были найдены тренировки для обновления параметра active. '
                         f'day - {day}, user_id - {user_id}')

    @classmethod
    async def update_in_progress_training_by_day(cls, user_id, day, in_progress):
        in_progress = boolean_dict[in_progress]

        await cur.execute(f"""
                                UPDATE trainings
                                SET
                                in_progress = {in_progress}
                                WHERE user_id = {user_id}
                                AND day = {day}
                                RETURNING id
                                """)
        get_id = await cur.fetchone()
        if get_id:
            logger.info(f'Параметр in_progress на тренировке дня {day} у пользователя с id = {user_id} '
                        f'был обновлен на {in_progress}.')
        else:
            logger.error(f'Не были найдены тренировки для обновления параметра in_progress. '
                         f'day - {day}, user_id - {user_id}')

    @classmethod
    async def get_trainings_by_day(cls, user_id, day):
        await cur.execute(f"""
            SELECT data, day, active
            FROM trainings
            WHERE user_id = {user_id}
            AND day = {day}
            """)
        trainings = await cur.fetchone()

        return trainings if trainings else (None, None, None)

    @classmethod
    async def get_next_training(cls, user_id, current_day):
        await cur.execute(f"""
                SELECT data, day, active
                FROM trainings
                WHERE user_id = {user_id}
                AND day > {current_day}
                ORDER BY day ASC
                """)
        trainings = await cur.fetchone()

        return trainings if trainings else (None, None, None)

    @classmethod
    async def get_prev_training(cls, user_id, current_day):
        await cur.execute(f"""
                SELECT data, day, active
                FROM trainings
                WHERE user_id = {user_id}
                AND day < {current_day}
                ORDER BY day DESC
                """)
        trainings = await cur.fetchone()

        return trainings if trainings else (None, None, None)

    @classmethod
    async def get_all_active_trainings_with_dates(cls):
        await cur.execute(f"""
                SELECT t.user_id, t.created_date, t.day
                FROM trainings t
                JOIN users u ON t.user_id = u.tg_id
                WHERE t.active = 1
                AND t.in_progress = 0
                """)
        active_trainigs_with_dates = await cur.fetchall()
        logger.info(f'Получено {len(active_trainigs_with_dates)} активных тренировок для напоминания')

        return [ReminderTraining(**res) for res in active_trainigs_with_dates]

    @classmethod
    async def get_active_training_by_user_id(cls, user_id):
        await cur.execute(f"""
            SELECT data, day
            FROM trainings
            WHERE active = 1
            AND user_id = {user_id}
            """)
        active_training = await cur.fetchone()
        if active_training:
            logger.info(f'Активная тренировка пользователя {user_id} была получена')
        else:
            logger.warning(f'У пользователя {user_id} нет активных тренировок')

        return active_training if active_training else (None, None)
