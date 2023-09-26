from loguru import logger

from gpt.chat import fill_prompt
from app.states import TimetableDays
import dal


async def process_prompt(user_id):
    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)

    timetable, recipes, trainings = await fill_prompt(data)

    await dal.Timetable.update_timetable(user_id, timetable)

    for day, recipe in recipes.items():
        await dal.Recipes.update_recipes(user_id, day, recipe)

    for day, training in trainings.items():
        await dal.Trainings.update_trainings(user_id, day, training)

    await TimetableDays.monday.set()
    timetable = await dal.Timetable.get_timetable(user_id)

    return timetable
