from loguru import logger
import asyncio

from gpt.chat import fill_prompt, fill_prompt_next_week, fill_meal_plan_prompt, fill_prompt_demo
from app.states import BaseStates
import app.keyboards as kb
import dal


async def process_prompt(user_id, client_changes=None):
    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)

    program, training = await fill_prompt(data, client_changes)
    await dal.Trainings.remove_prev_trainings(
        user_id=int(user_id)
    )
    training = training.replace('"', '').replace("""'""", '')
    training = replace_nth_occ(training, '**', '</b>', 2)
    training = training.replace('**', '<b>')
    training = training.replace('Подъемы', 'Подъем').replace('Разводка', 'Разведение')
    training = training.split('\n')

    day_number = 1
    final_training = []

    for line in training:
        if 'День' in line:
            continue
        if len(line) < 5 or 'Разминка' in line:
            final_training.append(line)
            continue

        exercise_name = line.split(' -')[0]
        exercise_name_words = exercise_name.replace('-', '').split()
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

    return program, final_training


async def proccess_meal_plan_prompt(user_id):
    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)

    meal_plan = await fill_meal_plan_prompt(data)

    meal_plan = replace_nth_occ(meal_plan, '**', '</b>', 2)
    meal_plan = meal_plan.replace('**', '<b>')

    await dal.Meals.insert_meal(
        user_id=int(user_id),
        day=1,
        meal_plan=meal_plan
    )

    return meal_plan


async def process_prompt_next_week(user_id, client_edits_next_week=None, demo=None):
    async def analyse_training(training):
        training = training.replace('"', '').replace("""'""", '')
        training = replace_nth_occ(training, '**', '</b>', 2)
        training = training.replace('**', '<b>')
        training = training.replace('Подъемы', 'Подъем').replace('Разводка', 'Разведение')
        training = training.split('\n')

        final_training = []

        for line in training:
            if 'День' in line:
                continue
            if len(line) < 45 or 'Разминка' in line:
                final_training.append(line)
                continue

            exercise_name = line.split(' -')[0]
            exercise_name_words = exercise_name.replace('-', '').split()
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

        return final_training

    logger.info(f'Отправляется промпт от пользователя с user_id = {user_id}')
    data = await dal.User.select_attributes(user_id)
    trainings_prev_week = ''
    for i in range(1, 8):
        if trainings_prev_week != '':
            trainings_prev_week += '\n\n'
        workout, _, _ = await dal.Trainings.get_trainings_by_day(user_id, i)
        if workout is None and trainings_prev_week != '':
            trainings_prev_week += f'День {i} - Отдых'
        else:
            trainings_prev_week += f'День {i} - {workout}'

    if demo:
        training = await fill_prompt_demo(data, trainings_prev_week, client_edits_next_week)
        final_training = await analyse_training(training)

        return final_training

    else:
        week = await dal.User.select_week(int(user_id))

        trainings = await fill_prompt_next_week(data, trainings_prev_week, week, client_edits_next_week)
        await dal.Trainings.remove_prev_trainings(
            user_id=int(user_id)
        )
        day_number = 1
        for training in trainings:
            if 'Отдых' in training:
                day_number += 1
            else:
                final_training = await analyse_training(training)

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
        return_to_training=False,
        skip_db=False
):
    from app.handlers import bot

    async def edit_message_text_def(text, chat_id, message_id, **kwargs):
        await bot.edit_message_text(text, chat_id, message_id, **kwargs)

    async def end_not_last_workout():
        training, day = await dal.Trainings.get_active_training_by_user_id(user_id)

        async with state.proxy() as data:
            next_training_in_days = int(day) - int(data['day'])

            if next_training_in_days % 100 == 1:
                day_word = 'день'
            elif next_training_in_days % 100 in [2, 3, 4]:
                day_word = 'дня'
            else:
                day_word = 'дней'

            await message.answer(f'Следующая тренировка ждёт вас через {next_training_in_days} {day_word}.')

    if user_id is None:
        user_id = message.from_user.id
    workout_in_process = workout_in_process.replace('<b>[ ', '').replace(' ]</b>', '')
    data['workout'] = workout_in_process.split(' кг')

    if data['weight_index'] == len(data['workout']) - 2:
        await state.set_state(BaseStates.show_trainings)

        try:
            await bot.delete_message(message.chat.id, data['temp_message'])
        except:
            pass

        for i in range(len(data['workout']) - 1):
            cur_segment = data['workout'][i].split('\n')[-1].split(' ')
            cur_segment = [x for x in cur_segment if x]
            name = ' '.join(cur_segment[:-2])
            weight = cur_segment[-1]

            if not skip_db:
                await dal.Exercises.add_exercise(name)
                await dal.UserResults.update_user_results(
                    user_id=user_id,
                    name=name,
                    weight=weight
                )

        week = await dal.User.select_week(user_id)
        if week == 0:
            await state.set_state(BaseStates.subscription_proposition)
            await edit_message_text_def(text=
                                        '🏆 Поздравляем с первой тренировкой! Первый шаг сделан.'
                                        '— Далее вы можете <b>посмотреть</b> как будет <b>выглядеть</b> '
                                        'одна из ваших <b>будущих тренировок</b> 7й - 9й недели.',
                                        chat_id=message.chat.id,
                                        message_id=data['message'],
                                        parse_mode='HTML',
                                        reply_markup=kb.first_training_proposition,
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
            training, new_day, active = await dal.Trainings.get_next_training(
                user_id=user_id,
                current_day=data['day']
            )
            if training:
                await dal.Trainings.update_active_training_by_day(
                    user_id=user_id,
                    day=new_day,
                    active=True
                )
                await end_not_last_workout()

            else:
                await state.set_state(BaseStates.subscription_proposition)

                await dal.User.increase_week_parameter(user_id)
                weeks_left = await dal.User.select_weeks_left(user_id)

                if weeks_left == 0:
                    await message.answer(
                        f'Вы завершили свою {week} неделю, и ваша подписка закончилась. '
                        f'Вам необходимо продлить подписку',
                        reply_markup=kb.subscribe
                    )

                else:
                    await state.set_state(BaseStates.end_of_week_changes)
                    temp_message = await message.answer('Перед составлением тренировок на следующую неделю, '
                                                        'напишите коррективы, которые вы бы хотели внести '
                                                        'в тренировки в целом '
                                                        '(до 100 символов)')
                    data['temp_message'] = temp_message.message_id

    else:
        if not return_to_training:
            data['weight_index'] += 1
        current_weight = data['workout'][data['weight_index']].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
        await edit_message_text_def(text=f'<b>День {data["day"]}</b>\n' +
                                         f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' +
                                         workout_in_process,
                                    chat_id=message.chat.id,
                                    message_id=data['message'],
                                    reply_markup=kb.insert_weights_in_workout,
                                    parse_mode='HTML'
                                    )


async def complete_training(
        workout_in_process,
        data,
        state,
        message,
        kb,
        user_id=None
):
    from app.handlers import bot

    async def edit_message_text_def(text, chat_id, message_id, **kwargs):
        await bot.edit_message_text(text, chat_id, message_id, **kwargs)

    async def end_not_last_workout():
        training, day = await dal.Trainings.get_active_training_by_user_id(user_id)

        async with state.proxy() as data:
            next_training_in_days = int(day) - int(data['day'])

            if next_training_in_days % 100 == 1:
                day_word = 'день'
            elif next_training_in_days % 100 in [2, 3, 4]:
                day_word = 'дня'
            else:
                day_word = 'дней'

            await message.answer(f'Следующая тренировка ждёт вас через {next_training_in_days} {day_word}.')

    await state.set_state(BaseStates.show_trainings)

    for i in range(len(data['workout']) - 1):
        workout_in_process = workout_in_process.replace('<b>[ ', '').replace(' ]</b>', '')
        data['workout'] = workout_in_process.split(' кг')

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

    await dal.Trainings.update_trainings(
        user_id=user_id,
        day=data['day'],
        data=workout_in_process,
        active=False
    )

    week = await dal.User.select_week(user_id)
    if week == 0:
        await state.set_state(BaseStates.subscription_proposition)
        await edit_message_text_def(text=
                                    '🏆 Поздравляем с первой тренировкой! Первый шаг сделан.'
                                    '— Далее вы можете <b>посмотреть</b> как будет <b>выглядеть</b> '
                                    'одна из ваших <b>будущих тренировок</b> 7й - 9й недели.',
                                    chat_id=message.chat.id,
                                    message_id=data['message'],
                                    parse_mode='HTML',
                                    reply_markup=kb.first_training_proposition,
                                    )
        await asyncio.sleep(1)
        return None

    await edit_message_text_def(text='🎉 Поздравляем с успешным завершением тренировки!',
                                chat_id=message.chat.id,
                                message_id=data['message']
                                )
    await asyncio.sleep(1)

    await message.answer('Помните, что здоровый сон (7-8 часов) и сбалансированное питание являются '
                         'обязательной частью программы, '
                         'без которой вы не сможете добиться желаемого результата!')
    await asyncio.sleep(1)

    subscribed = await dal.User.check_sub_type_by_user_id(user_id)

    training, new_day, active = await dal.Trainings.get_next_training(
        user_id=user_id,
        current_day=data['day']
    )
    if training:
        await dal.Trainings.update_active_training_by_day(
            user_id=user_id,
            day=new_day,
            active=True
        )
        await end_not_last_workout()

    else:
        if not subscribed:
            await state.set_state(BaseStates.subscription_proposition)

            await dal.User.increase_week_parameter(user_id)
            weeks_left = await dal.User.select_weeks_left(user_id)

            if weeks_left == 0:
                await message.answer(
                    f'Вы завершили свою {week} неделю, и ваша подписка закончилась. '
                    f'Вам необходимо продлить подписку',
                    reply_markup=kb.subscribe
                )

        else:
            await state.set_state(BaseStates.end_of_week_changes)
            temp_message = await message.answer('Перед составлением тренировок на следующую неделю, '
                                                'напишите коррективы, которые вы бы хотели внести '
                                                'в тренировки в целом '
                                                '(до 100 символов)')
            data['temp_message'] = temp_message.message_id


async def get_training_markup(user_id, day, ):
    next_training, _, _ = await dal.Trainings.get_next_training(
        user_id=user_id,
        current_day=day
    )

    reply_markup = kb.trainings_tab
    if next_training is None:
        reply_markup = kb.trainings_tab_without_next

    else:
        prev_training, _, _ = await dal.Trainings.get_prev_training(
            user_id=user_id,
            current_day=day
        )
        if prev_training is None:
            reply_markup = kb.trainings_tab_without_prev

    return reply_markup


def replace_nth_occ(string, sub, replace_string, n):
    find = string.find(sub)
    i = 1
    while find != -1:
        if i == n:
            string = string[:find]+replace_string+string[find + len(sub):]
            i = 0
        find = string.find(sub, find + len(sub) + 1)
        i += 1
    return string
