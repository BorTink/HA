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

from utils import process_prompt
from .states import PersonChars, timetable_states_list, timetable_states_str_list, TimetableDays, days_translation
from app import keyboards as kb
import dal
from gpt.chat_upgraded import UpgradedChatBot
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
            'Добро пожаловать! Я виртуальный тренер Health AI. Помогу составить сбалансированные планы тренировок '
            'под ваши индивидуальные запросы. С моей помощью вы сможете разработать эффективную программу занятий '
            'и легко отслеживать свой прогресс. ',
            reply_markup=kb.main_new)


@dp.callback_query_handler(state='*', text='generate_trainings')
async def generate_trainings(callback: types.CallbackQuery):
    await callback.message.answer(
        'Подождите, составляем ваши персональные тренировки...'
    )

    for attempt_number in range(3):
        trainings = await process_prompt(
            user_id=callback.from_user.id
        )
        answer_text = 'Вот ваше расписание тренировок:\n\n'
        for i, training in enumerate(trainings):
            answer_text += f'День {i}\n\n{training}'
            answer_text += '\n\n' if i == len(trainings) - 1 else ''
        await callback.message.answer(
            answer_text,
            reply_markup=kb.trainings_tab
        )
        break


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

    await state.set_state(TimetableDays.monday)
    await callback.message.answer(
        'Выберите действие'
        ' (ВНИМАНИЕ: в этом прототипе на пересоздание расписания есть лишь 1 попытка)',
        reply_markup=kb.main
    )


# ----- УПРАВЛЕНИЕ РАСПИСАНИЕМ ---------


@dp.callback_query_handler(state='*', text='lookup_data')
async def get_data(callback: types.CallbackQuery):
    user = await dal.User.select_attributes(callback.from_user.id)

    logger.info(f'Составляется расписание для {callback.from_user.id}')
    await callback.message.answer(
        'Наш искусственный интеллект составляет вам расписание \n'
        'Подождите около 4 минут'
    )
    for attempt_number in range(3):
        try:
            timetable = await process_prompt(
                user_id=callback.from_user.id
            )
            await callback.message.answer(
                f'Ваше расписание на понедельник:\n{timetable.monday}',
                reply_markup=kb.timetable
            )
            break
        except Exception as exc:
            logger.error(f'При обработке промпта произошла ошибка - {exc}. Попытка {attempt_number + 1}')
            if attempt_number == 2:
                raise Exception
                # await callback.message.answer(
                #     'При создании расписания произошла ошибка'
                # )


@dp.callback_query_handler(state=timetable_states_list, text=['SHOW_TIMETABLE', 'back_to_timetable'])
async def show_timetable(callback: types.CallbackQuery, state: FSMContext):
    timetable = await dal.Timetable.get_timetable(callback.from_user.id)
    state_name = await state.get_state()
    day_of_week = state_name.split(":")[1]

    await callback.message.answer(
        f'Ваше расписание на {days_translation[day_of_week]}:\n{eval(f"timetable.{day_of_week}")}',
        reply_markup=kb.timetable
    )


@dp.callback_query_handler(state=timetable_states_list, text=['show_next_day', 'show_prev_day'])
async def show_timetable(callback: types.CallbackQuery, state: FSMContext):
    state_name = await state.get_state()
    if callback.data == 'show_next_day':
        state_index = timetable_states_str_list.index(state_name)
        if state_index == len(timetable_states_str_list) - 1:
            await state.set_state(TimetableDays.monday)
            day_of_week = 'monday'
        else:
            day_of_week = timetable_states_str_list[state_index + 1].split(':')[1]
            await state.set_state(eval(f'TimetableDays.{day_of_week}'))

    elif callback.data == 'show_prev_day':
        state_index = timetable_states_str_list.index(state_name)
        if state_index == 0:
            await state.set_state(TimetableDays.sunday)
            day_of_week = 'sunday'
        else:
            day_of_week = timetable_states_str_list[state_index - 1].split(':')[1]
            await state.set_state(eval(f'TimetableDays.{day_of_week}'))
    else:
        logger.error(f'Некорректная data в callback_query - {callback.data}')
        raise Exception

    timetable = await dal.Timetable.get_timetable(callback.from_user.id)
    await callback.message.answer(
        f'Ваше расписание на {days_translation[day_of_week]}:\n{eval(f"timetable.{day_of_week}")}',
        reply_markup=kb.timetable
    )


# ----- АНКЕТА ПОЛЬЗОВАТЕЛЯ ---------


@dp.callback_query_handler(state='*', text=['update_data', 'insert_data'])
async def create_edit(callback: types.CallbackQuery):
    await callback.message.answer(
        'Пожалуйста, ответьте на пару вопросов, чтобы я смог составить вам персональную тренировку.'
    )
    sleep(0.5)
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
            'Каких результатов вы ожидаете от тренировок? (Например, скинуть вес или набрать мышечную массу) '
            'Напишите до 100 символов:'
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
            'Каких результатов вы ожидаете от тренировок? (Например, скинуть вес или набрать мышечную массу) '
            'Напишите до 100 символов:'
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
            'Каких результатов вы ожидаете от тренировок? (Например, скинуть вес или набрать мышечную массу) '
            'Напишите до 100 символов:'
        )
        await PersonChars.goals.set()


@dp.message_handler(state=PersonChars.goals)
async def add_goal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['goals'] = message.text

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
        'Сколько раз в неделю вы готовы заниматься '
        '(Рекомендованное количество: 2-4 дня в неделю):',
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
    await state.finish()

    await callback.message.answer(
        'Подождите, составляем ваши персональные тренировки...'
    )

    for attempt_number in range(3):
        trainings = await process_prompt(
            user_id=callback.from_user.id
        )
        answer_text = 'Вот ваше расписание тренировок:\n\n'
        for i, training in enumerate(trainings):
            answer_text += f'День {i+1}\n\n{training}'
            answer_text += '\n\n' if i == len(trainings)-1 else ''
        await callback.message.answer(
            answer_text,
            reply_markup=kb.trainings_tab
        )
        break


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


@dp.message_handler(state='*')
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
