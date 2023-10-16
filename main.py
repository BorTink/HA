import os

from aiogram import executor
from loguru import logger

from app.handlers import dp
import dal


async def on_startup(_):
    await dal.User.db_start()
    await dal.Timetable.create_timetable()
    await dal.Exercises.create_exercises()
    await dal.UserResults.create_user_results()
    await dal.Trainings.create_trainings()
    logger.info(f'Бот успешно запущен!')


if __name__ == '__main__':
    LOG_FILE_NAME = os.path.dirname(os.path.realpath(__file__)) + '/log/health_ai.log'
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
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True, timeout=None)
