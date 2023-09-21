import os

from aiogram import executor
from loguru import logger
import datasets

from app.handlers import dp
import dal


async def on_startup(_):
    await dal.User.db_start()
    await dal.Timetable.create_timetable()
    await dal.Recipes.create_recipes()
    await dal.ShoppingList.create_shopping_list()
    await dal.Trainings.create_trainings()
    print('Бот успешно запущен!')


if __name__ == '__main__':
    LOG_FILE_NAME = os.path.dirname(os.path.realpath(__file__)) + '/log/health_ai.log'
    logger.add(
        LOG_FILE_NAME,
        level='DEBUG',
        rotation='30 MB',

        backtrace=False,
        catch=False,
        diagnose=False,
        compression='zip'
    )

    logger.opt(exception=False)

    with logger.contextualize(ip=None, path=None, method=None):
        datasets.disable_caching()
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True, timeout=None)
