from loguru import logger
import asyncio

from gpt.chat import fill_prompt
from app.states import BaseStates
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
                data=training.replace('"', '').replace("""'""", '')
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


async def process_workout(
        workout_in_process,
        data,
        state,
        message,
        kb,
        user_id=None
):
    if user_id is None:
        user_id = message.from_user.id
    workout_in_process = workout_in_process.replace('*', '')
    data['workout'] = workout_in_process.split(' кг')

    if data['weight_index'] == len(data['workout']) - 2:
        await state.set_state(BaseStates.show_trainings)

        for i in range(len(data['workout']) - 1):
            cur_segment = data['workout'][i].split('\n')[-1].split(' ')
            name = ' '.join(cur_segment[:-2])
            weight = cur_segment[-1]

            next_segment = data['workout'][i + 1].split('\n')[0].split(' ')
            sets = next_segment[1]
            reps = next_segment[3]
            await dal.Exercises.add_exercise(name)
            await dal.UserResults.update_user_results(
                user_id=user_id,
                name=name,
                sets=sets,
                weight=weight,
                reps=reps
            )

        await message.answer('Вы закончили тренировку')
        await asyncio.sleep(0.5)
        await dal.Trainings.update_trainings(
            user_id=user_id,
            day=data['day'],
            data=workout_in_process,
            active=False
        )
        training, new_day = await dal.Trainings.get_next_training(
            user_id=user_id,
            current_day=data['day']
        )
        if training:
            await dal.Trainings.update_active_training_by_day(
                user_id=user_id,
                day=new_day,
                active=True
            )
        else:
            await message.answer('Вы закончили все тренировки на этой неделе')
            await asyncio.sleep(2)
            training, new_day = await dal.Trainings.get_trainings_by_day(
                user_id=user_id,
                day=1
            )

        data['workout'] = training
        data['day'] = new_day

        await message.answer(
            training,
            reply_markup=kb.trainings_tab
        )
    else:
        await state.set_state(BaseStates.start_workout)
        data['weight_index'] += 1
        current_weight = data['workout'][data['weight_index']].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
        await message.answer(
            workout_in_process,
            reply_markup=kb.insert_weights_in_workout,
            parse_mode='Markdown'
        )
