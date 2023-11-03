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


async def split_workout(workout, weight_index, weight_value):
    part_before_kg = workout[weight_index].split(' ')
    workout_in_process = ' '.join(part_before_kg[:-1]) + f' *{weight_value}*' + ' кг'

    first_half = ' кг'.join(workout[0:weight_index])
    if first_half:
        first_half += ' кг'
    workout_in_process = first_half + workout_in_process + ' кг'.join(workout[weight_index + 1:])

    return workout_in_process
