from aiogram import executor

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
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True, timeout=None)
