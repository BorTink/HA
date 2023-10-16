from loguru import logger

from gpt.chat import fill_prompt
from app.states import TimetableDays
import dal


async def process_prompt(user_id):
    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)

    trainings = await fill_prompt(data)
    for i in trainings:
        await dal.Trainings.update_trainings(
            user_id=user_id,
            day=i+1,
            data=trainings[i],
            is_rest=True if trainings[i] == 'Отдых' else False
        )

    return trainings
