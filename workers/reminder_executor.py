from datetime import datetime
import asyncio

from loguru import logger

from reminder import Reminder
import dal

reminder = Reminder()


async def enable_reminder():
    await dal.User.db_start()
    await dal.Exercises.create_exercises()
    await dal.UserResults.create_user_results()
    await dal.Trainings.create_trainings()
    logger.info(f'Сервис по напоминаниям успешно запущен!')
    while True:
        await reminder()
        await asyncio.sleep(120)


if __name__ == '__main__':

    asyncio.run(enable_reminder())
