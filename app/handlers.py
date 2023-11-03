import time
from time import sleep
import os

import tiktoken
from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types.message import ContentType

from dotenv import load_dotenv
from loguru import logger

from utils import process_prompt, split_workout
from .states import PersonChars, BaseStates
from app import keyboards as kb
import dal
from gpt.chat import ChatGPT

# ----- СТАРТ И ПОДПИСКА ---------

load_dotenv()
bot = Bot(os.getenv('TOKEN'))

dp = Dispatcher(bot=bot, storage=MemoryStorage())  # storage впоследствии изменить на redis
dp.middleware.setup(LoggingMiddleware())

PRICE = types.LabeledPrice(label='Подписка на 1 месяц', amount=500*100)


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message, state: FSMContext):
    if state:
        await state.finish()
    logger.info('start')
    user = await dal.User.select_attributes(message.from_user.id)
    logger.info(f'user - {user}')

    if user:
        await message.answer('Здравствуйте!', reply_markup=kb.always_markup)
        await message.answer('Выберите действие',
                             reply_markup=kb.main)
    else:
        await message.answer(
            '👋 Добро пожаловать! Я виртуальный тренер Health AI. Помогу составить сбалансированные планы тренировок '
            'под ваши индивидуальные запросы.',
            parse_mode='Markdown'
        )
        sleep(1)
        await message.answer(
            'С моей помощью вы сможете разработать эффективную программу занятий и легко отслеживать свой прогресс.',
            parse_mode='Markdown'
        )
        sleep(1)
        await message.answer(
            '_Тренировки, разработанные Health AI, основаны на научных работах и советах профессиональных тренеров, '
            'но несут исключительно рекомендательный характер._',
            parse_mode='Markdown'
        )
        sleep(1)
        await message.answer(
            '_Мы не несём ответственности за травмы, которые могут быть получены в процессе выполнения упражнений._',
            reply_markup=kb.main_new,
            parse_mode='Markdown'
        )


@dp.callback_query_handler(state='*', text='generate_trainings')
async def generate_trainings(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        '⏳Подождите, составляем персональную тренировку'
    )

    await state.set_state(BaseStates.show_trainings)

    await process_prompt(
        user_id=callback.from_user.id
    )
    training, new_day = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await callback.message.answer(
        '✅ План вашей первой тренировки готов! Попробуйте его выполнить и возвращайтесь с обратной связью!'
    )
    sleep(2)
    await callback.message.answer(
        training,
        reply_markup=kb.trainings_tab
    )


@dp.message_handler(state='*', text='Купить подписку')
async def buy_subscription(message: types.Message, state: FSMContext):
    if os.getenv('PAYMENTS_TOKEN').split(':')[1] == 'TEST':
        await message.answer('Тестовый платеж!')

    await bot.send_invoice(message.chat.id,
                           title='Подписка на бота',
                           description='Подписка на бота на 1 месяц',
                           provider_token=os.getenv('PAYMENTS_TOKEN'),
                           currency='rub',
                           photo_url='https://img.freepik.com/premium-photo/this-sleek-minimalist-home-gym-features-floortoceiling-windows-that-allow-abundant-natural-light-illuminate-space-generated-by-ai_661108-5016.jpg',
                           photo_width=1270,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter='one-month-subscription',
                           payload='test-invoice-payload')


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    logger.info(f'Оплата у пользователя {message.from_user.id} прошла успешно')
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        logger.info(f'{k} - {v}')

    await message.answer(f'Платеж на сумму {message.successful_payment.total_amount // 100} '
                         f'{message.successful_payment.currency} прошел успешно')


@dp.callback_query_handler(state='*', text='back_to_menu')
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    if state:
        await state.finish()

    await callback.message.answer(
        'Выберите действие',
        reply_markup=kb.main
    )


# ----- УПРАВЛЕНИЕ РАСПИСАНИЕМ ---------


@dp.callback_query_handler(state='*', text=['SHOW_TIMETABLE', 'back_to_timetable'])
async def show_timetable(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BaseStates.show_trainings)

    training, day = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await callback.message.answer(
        training,
        reply_markup=kb.trainings_tab
    )


@dp.callback_query_handler(state='*', text=['next_workout', 'prev_workout'])
async def switch_days(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if callback.data == 'next_workout':
            training, new_day = await dal.Trainings.get_next_training(
                user_id=callback.from_user.id,
                current_day=data['day']
            )
            if training:
                data['day'] = new_day
                data['workout'] = training
                await callback.message.answer(
                    training,
                    reply_markup=kb.trainings_tab
                )
            else:
                training, new_day = await dal.Trainings.get_trainings_by_day(
                    user_id=callback.from_user.id,
                    day=1
                )
                data['day'] = 1
                data['workout'] = training

                await callback.message.answer(
                    training,
                    reply_markup=kb.trainings_tab
                )

        elif callback.data == 'prev_workout':
            training, new_day = await dal.Trainings.get_prev_training(
                user_id=callback.from_user.id,
                current_day=data['day']
            )
            if training:
                data['day'] = new_day
                data['workout'] = training

                await callback.message.answer(
                    training,
                    reply_markup=kb.trainings_tab
                )
            else:
                training, new_day = await dal.Trainings.get_prev_training(
                    user_id=callback.from_user.id,
                    current_day=1000000
                )
                data['day'] = new_day
                data['workout'] = training

                await callback.message.answer(
                    training,
                    reply_markup=kb.trainings_tab
                )
        else:
            logger.error(f'Некорректная data в callback_query - {callback.data}')
            raise Exception


@dp.callback_query_handler(state=BaseStates.show_trainings, text='rebuild_workouts')
async def ask_client_for_changes(callback: types.CallbackQuery, state: FSMContext):
    user = await dal.User.select_attributes(callback.from_user.id)
    if user.rebuilt == 1:
        await callback.message.answer(
            'Вы уже пересобирали тренировку на неделю'
        )
    else:
        await callback.message.answer(
            'Введите что вы хотите изменить до 100 символов. '
            '(Тренировку можно пересобрать 1 раз в пробной версии, может добавить нужные упражнения или что-то убрать)'
        )
        await state.set_state(BaseStates.rebuild_workouts)


@dp.message_handler(state=BaseStates.rebuild_workouts)
async def rebuild_workouts(message: types.Message, state: FSMContext):
    await message.answer(
        '⏳Подождите, пересобираем персональную тренировку'
    )

    await state.set_state(BaseStates.show_trainings)

    await dal.User.update_rebuilt_parameter(message.from_user.id)

    await process_prompt(
        user_id=message.from_user.id,
        client_changes=message.text
    )
    training, new_day = await dal.Trainings.get_trainings_by_day(
        user_id=message.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await message.answer(
        training,
        reply_markup=kb.trainings_tab
    )


@dp.callback_query_handler(state=BaseStates.show_trainings, text='start_workout')
async def prestart_workout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        '☝️ Помните, что указанный в упражнениях вес является приблизительным. '
        'Если вам тяжело или легко выполнять заданное количество упражнений с каким-то весом, '
        'поменяйте его исходя из ваших возможностей.'
    )
    sleep(1)
    await callback.message.answer(
        'При возникновении любых проблем обязательно проконсультируйтесь с лицензированным специалистом!'
    )
    sleep(1)
    await state.set_state(BaseStates.start_workout)
    async with state.proxy() as data:
        data['weight_index'] = 0
        data['workout'] = data['workout'].split(' кг')
    await callback.message.answer(
        '☝После того, как пройдете тренировку (или по ходу выполнения упражнений), '
        'обязательно введите свои показатели, чтобы усовершенствовать будущие занятия. '
        'Это поможет при расчёте оптимальных нагрузок и времени восстановления.\nХорошей тренировки!',
        reply_markup=kb.start_workout
    )


@dp.callback_query_handler(state=BaseStates.start_workout, text='insert_weights')
async def begin_workout(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        current_weight = data['workout'][0].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
        await callback.message.answer(
            workout_in_process,
            reply_markup=kb.insert_weights_in_workout,
            parse_mode='Markdown'
        )


@dp.callback_query_handler(state=BaseStates.start_workout, text='add_weight')
async def add_weight(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BaseStates.add_weight)
    await callback.message.answer(
        'Введите новый вес'
    )


@dp.message_handler(state=BaseStates.add_weight)
async def add_weight(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    elif int(message.text) > 300:
        await message.answer('Похоже вы опечатались, перевведите значение')
    else:
        async with state.proxy() as data:
            workout_in_process = await split_workout(data['workout'], data['weight_index'], int(message.text))
            workout_in_process = workout_in_process.replace('*', '')
            data['workout'] = workout_in_process.split(' кг')

            if data['weight_index'] == len(data['workout']) - 2:
                await state.set_state(BaseStates.show_trainings)

                for i in range(len(data['workout'])-1):
                    cur_segment = data['workout'][i].split('\n')[-1].split(' ')
                    name = ' '.join(cur_segment[:-2])
                    weight = cur_segment[-1]

                    next_segment = data['workout'][i+1].split('\n')[0].split(' ')
                    sets = next_segment[1]
                    reps = next_segment[3]
                    await dal.Exercises.add_exercise(name)
                    await dal.UserResults.update_user_results(
                        user_id=message.from_user.id,
                        name=name,
                        sets=sets,
                        weight=weight,
                        reps=reps
                    )

                await message.answer('Вы закончили тренировку')
                sleep(0.5)
                await dal.Trainings.update_trainings(message.from_user.id, data['day'], workout_in_process, False)
                training, new_day = await dal.Trainings.get_trainings_by_day(
                    user_id=message.from_user.id,
                    day=1
                )
                data['workout'] = training

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

# ----- АНКЕТА ПОЛЬЗОВАТЕЛЯ ---------


@dp.callback_query_handler(state='*', text=['update_data', 'insert_data'])
async def create_edit(callback: types.CallbackQuery):
    await callback.message.answer(
        '🏃 Начинаем пробный период! Туда включён план тренировок на первую неделю и возможность 1 раз пересобрать его.' 
        'После завершения пробного периода вам будет предложено оформить подписку для продолжения занятий и доступа к '
        'продвинутому функционалу.'
    )
    sleep(1)
    await callback.message.answer(
        """
       💬 Пожалуйста, пройдите небольшую анкету, чтобы я смог составить вам план персональных тренировок на эту неделю.
        """
    )
    sleep(1)
    await callback.message.answer(
        'Укажите свой пол',
        reply_markup=kb.gender
    )
    await PersonChars.gender.set()


@dp.callback_query_handler(state=PersonChars.gender)
async def add_sex(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'gender_man':
        async with state.proxy() as data:
            data['gender'] = 'Мужской'
    if callback.data == 'gender_woman':
        async with state.proxy() as data:
            data['gender'] = 'Женский'

    await callback.message.answer('Введите свой возраст (Полных лет)')
    await PersonChars.age.set()


@dp.message_handler(state=PersonChars.age)
async def add_age(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['age'] = int(message.text)

        await message.answer(
            'Укажите свой рост (см)'
        )
        await PersonChars.height.set()


@dp.message_handler(state=PersonChars.height)
async def add_height(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['height'] = int(message.text)

        await message.answer(
            'Введите свой вес (кг)'
        )
        await PersonChars.weight.set()


@dp.message_handler(state=PersonChars.weight)
async def add_weight(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['weight'] = int(message.text)

        await message.answer(
            'Оцените ваш уровень физической подготовки',
            reply_markup=kb.gym_experience
        )
        await PersonChars.gym_experience.set()


@dp.callback_query_handler(state=PersonChars.gym_experience)
async def add_gym_experience(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['gym_experience'] = callback.data
    if callback.data in ['medium', 'experienced']:
        await callback.message.answer(
            'Знаете ли вы свои макимальные показатели веса в жиме лежа, становой тяге и приседаниях со штангой?',
            reply_markup=kb.max_results
        )
        await PersonChars.max_results.set()
    else:
        await callback.message.answer(
            'Каких результатов вы ожидаете от тренировок?',
            reply_markup=kb.expected_results
        )
        await PersonChars.goals.set()


@dp.callback_query_handler(state=PersonChars.max_results)
async def ask_max_results(callback: types.CallbackQuery):
    if callback.data == 'yes':
        await callback.message.answer(
            'Укажите максимальный вес в жиме лежа (Учитывая вес штанги 20 кг, указать в кг):'
        )
        await PersonChars.bench_results.set()

    if callback.data == 'no':
        await callback.message.answer(
            'Каких результатов вы ожидаете от тренировок?',
            reply_markup=kb.expected_results
        )
        await PersonChars.goals.set()


@dp.message_handler(state=PersonChars.bench_results)
async def add_bench_results(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['bench_results'] = int(message.text)

        await message.answer(
            'Укажите максимальный вес в становой тяге (Учитывая вес штанги 20 кг, указать в кг).'
        )
        await PersonChars.deadlift_results.set()


@dp.message_handler(state=PersonChars.deadlift_results)
async def add_deadlift_results(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['deadlift_results'] = int(message.text)

        await message.answer(
            'Укажите максимальный вес в приседаниях со штангой (Учитывая вес штанги 20 кг, указать в кг).'
        )
        await PersonChars.squats_results.set()


@dp.message_handler(state=PersonChars.squats_results)
async def add_squats_results(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['squats_results'] = int(message.text)

        await message.answer(
            'Каких результатов вы ожидаете от тренировок? (Например, скинуть вес или набрать мышечную массу)',
            reply_markup=kb.expected_results
        )
        await PersonChars.goals.set()


@dp.callback_query_handler(state=PersonChars.goals)
async def add_goal(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['goals'] = callback.data

    await callback.message.answer(
        'Хотите ли вы прокачать какие-то отдельные части тела больше? Напишите до 100 символов'
    )
    await PersonChars.focus.set()


@dp.message_handler(state=PersonChars.focus)
async def add_squats_results(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['goals'] += '. Additionally, ' + message.text

    await message.answer(
        'Насколько интенсивно вы готовы заниматься? Укажите интенсивность тренировок.',
        reply_markup=kb.intensity
    )
    await PersonChars.intensity.set()


@dp.callback_query_handler(state=PersonChars.intensity)
async def add_intensity(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['intensity'] = callback.data

    await callback.message.answer(
        'Есть ли у вас какие-нибудь противопоказания к тренировкам? Если да, то укажите какие '
        '(Например: травмы, растяжения, проблемы с позвоночником, высокое артериальное давление).'
        'Напишите до 100 символов.'
    )
    await PersonChars.health_restrictions.set()


@dp.message_handler(state=PersonChars.health_restrictions)
async def add_intensity(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['health_restrictions'] = message.text

    await message.answer(
        'Укажите одним числом сколько раз в неделю вы готовы заниматься. '
        '(Рекомендованное количество: 3-4 дня в неделю, ввести возможно от 2 до 4 дней)',
        reply_markup=kb.times_per_week
    )

    await PersonChars.times_per_week.set()


@dp.callback_query_handler(state=PersonChars.times_per_week)
async def add_times_per_week(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['times_per_week'] = int(callback.data)
        if 'squats_results' not in data.keys():
            data['squats_results'] = 'none'
        if 'deadlift_results' not in data.keys():
            data['deadlift_results'] = 'none'
        if 'bench_results' not in data.keys():
            data['bench_results'] = 'none'

    await dal.User.add_attributes(state, callback.from_user.id)
    await state.set_state(BaseStates.show_trainings)

    await callback.message.answer(
        '⏳Подождите, составляем персональную тренировку'
    )

    await process_prompt(
        user_id=callback.from_user.id
    )
    training, new_day = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await callback.message.answer(
        '✅ План вашей первой тренировки готов! Попробуйте его выполнить и возвращайтесь с обратной связью!'
    )
    sleep(2)
    await callback.message.answer(
        training,
        reply_markup=kb.trainings_tab
    )


# ----- ОБЫЧНЫЙ ChatGPT ---------


# ВЕРСИЯ ЧАТА С ДООБУЧЕНИЕМ

# @dp.message_handler(state='*')
# async def answer(message: types.Message, state: FSMContext):
#     global gpt_bot
#     try:
#         print(type(gpt_bot))
#     except Exception:
#         gpt_bot = UpgradedChatBot()
#
#     await message.reply('Сейчас..')
#     text = message.text
#     reply = gpt_bot.chatbot(text)
#
#     await message.reply(reply)


@dp.message_handler(state=None)
async def answer(message: types.Message):
    try:
        encoding = tiktoken.get_encoding('cl100k_base')
        prompt_num_tokens = len(encoding.encode(message.text))
        logger.info(f'Сообщение от user_id {message.from_user.id} - {message.text}')

        logger.info(f'Длина промпта для расписания '
                    f'- {prompt_num_tokens} токенов')
        await message.reply(f'Длина промпта для расписания '
                    f'- {prompt_num_tokens} токенов')

        reply = ChatGPT().chat(message.text)
        reply_num_tokens = len(encoding.encode(reply))
        await message.answer(f'Длина ответа '
                    f'- {reply_num_tokens} токенов. '
                    f'В сумме вышло {prompt_num_tokens + reply_num_tokens} токенов')

        logger.info(f'Длина ответа '
                    f'- {reply_num_tokens} токенов. '
                    f'В сумме вышло {prompt_num_tokens + reply_num_tokens} токенов')

        logger.info(f'Ответ - {reply}')
        await message.reply(reply)
    except Exception as exc:
        logger.info(f'Ошибка - {exc}')
        await message.reply(f'При генерации ответа произошла ошибка - {exc}')
