from loguru import logger

from gpt.chat_upgraded import fill_prompt
from app.states import TimetableDays
import dal


async def process_prompt(user_id):
    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)

    timetable, recipes, shopping_list, trainings = await fill_prompt(data)
    await dal.Timetable.update_timetable(user_id, timetable)
    await dal.Recipes.update_recipes(user_id, 'monday', recipes)
    await dal.ShoppingList.update_shopping_list(user_id, shopping_list)
    await dal.Trainings.update_trainings(user_id, 'monday', trainings)

    await TimetableDays.monday.set()
    timetable = await dal.Timetable.get_timetable(user_id)

    return timetable
