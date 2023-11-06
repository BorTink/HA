import os

from loguru import logger
import asyncio

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
    LOG_FILE_NAME = os.path.dirname(os.path.realpath(__file__)) + '/log/reminder.log'
    logger.add(
        LOG_FILE_NAME,
        level='DEBUG',
        rotation='3 MB',

        backtrace=False,
        catch=False,
        diagnose=False,
        compression='zip'
    )

    logger.opt(exception=False)

    with logger.contextualize(ip=None, path=None, method=None):
        asyncio.run(enable_reminder())
