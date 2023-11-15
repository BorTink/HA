from loguru import logger
import asyncio

from gpt.chat import fill_prompt
from app.states import BaseStates
import app.keyboards as kb
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
            cur_training = training.replace('"', '').replace("""'""", '')
            cur_training = cur_training.replace('Подъемы', 'Подъем').replace('Разводка', 'Разведение').split('\n')[1:]

            final_training = []
            for line in cur_training:
                if len(line) < 5 or 'Разминка' in line:
                    final_training.append(line)
                    continue

                exercise_name = line.split(' -')[0]
                exercise_name_words = exercise_name.split()
                similar_exercises = await dal.Exercises.get_all_similar_exercises_by_word(exercise_name_words.pop(0))

                if similar_exercises:
                    temp_exercises = []

                    for word in exercise_name_words:
                        for exercise in similar_exercises:
                            if word in exercise.name:
                                temp_exercises.append(exercise)

                        if not temp_exercises:
                            break

                        similar_exercises = temp_exercises
                        temp_exercises = []

                    min_len_word = 100000
                    final_exercise = None
                    for exercise in similar_exercises:
                        if len(exercise.name) < min_len_word:
                            min_len_word = len(exercise.name)
                            final_exercise = exercise

                    exercise_name = f'<a href="{final_exercise.link}">{exercise_name}</a>'

                final_training.append(f'{exercise_name} -{" -".join(line.split(" -")[1:])}')

            final_training = '\n'.join(final_training)

            await dal.Trainings.update_trainings(
                user_id=int(user_id),
                day=day_number,
                data=final_training
            )
            day_number += 1

    return trainings


async def split_workout(workout, weight_index, weight_value):
    part_before_kg = workout[weight_index].split(' ')
    workout_in_process = ' '.join(part_before_kg[:-1]) + f' <b>[ {weight_value} ]</b>' + ' кг'

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
        user_id=None,
        return_to_training=False
):
    from app.handlers import bot

    async def edit_message_text_def(text, chat_id, message_id, **kwargs):
        await bot.edit_message_text(text, chat_id, message_id, **kwargs)

    if user_id is None:
        user_id = message.from_user.id
    workout_in_process = workout_in_process.replace('<b>[ ', '').replace(' ]</b>', '')
    data['workout'] = workout_in_process.split(' кг')

    if data['weight_index'] == len(data['workout']) - 2:
        await state.set_state(BaseStates.show_trainings)

        for i in range(len(data['workout']) - 1):
            cur_segment = data['workout'][i].split('\n')[-1].split(' ')
            cur_segment = [x for x in cur_segment if x]
            name = ' '.join(cur_segment[:-2])
            weight = cur_segment[-1]

            await dal.Exercises.add_exercise(name)
            await dal.UserResults.update_user_results(
                user_id=user_id,
                name=name,
                weight=weight
            )

        first_training = await dal.User.check_if_first_training_by_user_id(user_id)
        if first_training:
            await edit_message_text_def(text='🎉 Поздравляем вас с первым успешным занятием!',
                                                  chat_id=message.chat.id,
                                                  message_id=data['message']
                                                  )
            await asyncio.sleep(1)

        else:
            await edit_message_text_def(text='🎉 Поздравляем с успешным завершением тренировки!',
                                                  chat_id=message.chat.id,
                                                  message_id=data['message']
                                                  )
            await asyncio.sleep(1)

        await message.answer('Помните, что здоровый сон (7-8 часов) и сбалансированное питание являются '
                             'обязательной частью программы, '
                             'без которой вы не сможете добиться желаемого результата!')
        await asyncio.sleep(1)

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

        subscribed = await dal.User.check_if_subscribed_by_user_id(user_id)
        if not subscribed and first_training:
            await dal.User.update_first_training_parameter(user_id)

            await message.answer(
                '🌟 Если вы не хотите стоять на месте и для вас важен прогресс в тренировках, '
                'рекомендуем оформить ежемесячную подписку!',
                reply_markup=kb.always_markup
            )
            await asyncio.sleep(1)
            await message.answer(
                '📈 Так вы сможете соразмерно увеличивать нагрузки и менять программу занятий '
                'для получения максимальной пользы.'
            )
            await asyncio.sleep(1)
            await message.answer("Основные преимущества подписки:\n"
                                 "▫️Регулярное обновление программы тренировок;\n"
                                 "▫️Высокая персонализация (с опорой на ваши результаты);\n"
                                 "▫️Повышенная эффективность от тренировок;\n"
                                 "▫️Возможность обновлять свои данные;\n"
                                 "▫️Поддержка на всём периоде занятий")
            await asyncio.sleep(1)
            await message.answer('Стоимость подписки 399 руб/мес.')
            await asyncio.sleep(1)
            await message.answer(
                'Оформляйте подписку на Health AI и меняйтесь к лучшему каждый день!',
                reply_markup=kb.subscribe_proposition
            )

        else:
            await message.answer('Возвращаемся к тренировкам', reply_markup=kb.always_markup)
            await asyncio.sleep(1.5)

            data['workout'] = training
            data['day'] = new_day

            await message.answer(
                f'День {data["day"]}\n' + training,
                reply_markup=kb.trainings_tab,
                parse_mode='HTML'
            )

    else:
        await state.set_state(BaseStates.start_workout)
        if not return_to_training:
            data['weight_index'] += 1
        current_weight = data['workout'][data['weight_index']].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
        await edit_message_text_def(text=f'День {data["day"]}\n' + workout_in_process,
                                    chat_id=message.chat.id,
                                    message_id=data['message'],
                                    reply_markup=kb.insert_weights_in_workout,
                                    parse_mode='HTML'
                                    )


async def get_training_markup(user_id, day, ):
    next_training, _ = await dal.Trainings.get_next_training(
        user_id=user_id,
        current_day=day
    )

    reply_markup = kb.trainings_tab
    if next_training is None:
        reply_markup = kb.trainings_tab_without_next

    else:
        prev_training, _ = await dal.Trainings.get_prev_training(
            user_id=user_id,
            current_day=day
        )
        if prev_training is None:
            reply_markup = kb.trainings_tab_without_prev

    return reply_markup
