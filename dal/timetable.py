from loguru import logger

from dal.user import User
import schemas


class Timetable:
    @classmethod
    async def create_timetable(cls):
        global db
        global cur
        db, cur = await User.get_db_cur()
        await cur.execute("""
                    CREATE TABLE IF NOT EXISTS timetable(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    tg_id TEXT, 
                    monday TEXT,
                    tuesday TEXT,
                    wednesday TEXT,
                    thursday TEXT,
                    friday TEXT,
                    saturday TEXT,
                    sunday TEXT
                    )
                    """)

    @classmethod
    async def update_timetable(cls, user_id, timetable: schemas.TimetableData):
        await cur.execute(f"""
        SELECT id
        FROM timetable
        WHERE tg_id = {user_id}
        """)
        user = await cur.fetchone()

        if user:
            logger.debug(f'Расписание пользователя с id = {user_id} было найдено, происходит обновление расписания')
            await cur.execute(f"""
                    UPDATE timetable
                    SET
                    (tg_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
                    =
                    ({user_id}, '{timetable.monday}', '{timetable.tuesday}', '{timetable.wednesday}',
                    '{timetable.thursday}', '{timetable.friday}', '{timetable.saturday}', '{timetable.sunday}')
                    """)
            logger.info(f'Расписание пользователя с id = {user_id} было обновлено.')

        else:
            logger.debug(f'Расписание пользователя с id = {user_id} не было найдено, создается новое расписание.')
            await cur.execute(f"""
                    INSERT INTO timetable
                    (tg_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
                    VALUES
                    ({user_id}, '{timetable.monday}', '{timetable.tuesday}', '{timetable.wednesday}',
                    '{timetable.thursday}', '{timetable.friday}', '{timetable.saturday}', '{timetable.sunday}')
                    """)
            logger.info(f'Расписание пользователя с id = {user_id} было создано.')

        await db.commit()

    @classmethod
    async def get_timetable(cls, user_id):
        await cur.execute(f"""
            SELECT monday, tuesday, wednesday, thursday, friday, saturday, sunday
            FROM timetable
            WHERE tg_id = {user_id}
            """)
        timetable = await cur.fetchone()

        return schemas.TimetableData(**dict(timetable))
