from loguru import logger

from gpt.chat import fill_prompt
import dal


async def process_prompt(user_id, client_changes=None):
    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)

    trainings = await fill_prompt(data, client_changes)
    await dal.Trainings.remove_prev_trainings(
        user_id=int(user_id)
    )
    day_number = 1
    for training in trainings:
        if 'Отдых' in training:
            day_number += 1
        else:
            await dal.Trainings.update_trainings(
                user_id=int(user_id),
                day=day_number,
                data=training.replace('"', '').replace("""'""", ''),
                is_rest=False
            )
        day_number += 1

    return trainings
