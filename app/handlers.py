import time
from time import sleep
import os

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
        await state.set_state(TimetableDays.monday)
        await message.answer('Здравствуйте!', reply_markup=kb.always_markup)
        await message.answer('Выберите действие'
                             ' (ВНИМАНИЕ: в этом прототипе на пересоздание расписания есть лишь 1 попытка)',
                             reply_markup=kb.main)
    else:
        await message.answer(
            '👨‍💼 Привет! Это ваш виртуальный тренер от Health AI, персональный помощник на пути'
            ' к здоровью и хорошей физической форме.')
        sleep(1)

        await message.answer(
            '👨🧬 Мы применяем передовые технологии искусственного интеллекта для создания'
            ' индивидуальных планов тренировок и питания,'
            ' адаптированных под ваши личные потребности и жизненный ритм.')
        sleep(1)

        await message.answer(
            '🚀 Благодаря нашему персональному подходу к составлению планов тренировок и питания вы сможете достигнуть'
            ' желаемых результатов куда легче, чем при использовании стандартных решений и шаблонных программ!')
        sleep(1)

        await message.answer(
            'С нами у вас будут: \n'
            '🌱 Гибкий план питания и тренировок под ваши цели \n'
            '🌱 Персональные рекомендации на основе ИИ \n'
            '🌱 Поддержка и мотивация весь период занятий \n'
            '🌱 Доступ к тренеру-ИИ 24/7')
        sleep(1)

        await message.answer(
            '👨“Пожалуйста, ответьте на пару вопросов для составления вашего '
            'индивидуального плана (около 3 минут).”', reply_markup=kb.main_new)


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


@dp.callback_query_handler(state='*', text=['update_data', 'insert_data'])
async def create_edit(callback: types.CallbackQuery):

    user = await dal.User.select_attributes(callback.from_user.id)
    if user:
        if user.attempts >= 2:
            logger.error('Превышено кол-во попыток на пересоздание расписания')
            await callback.message.answer(
                'Количество попыток на создание расписания в тестовой версии ограничено 2 попытками,'
                ' пересоздать расписание невозможно'
            )
            return None

        await dal.User.increase_attempts_by_user_id(callback.from_user.id)

    await callback.message.answer(
        'Укажите ваш пол (выберите в меню)',
        reply_markup=kb.gender
    )
    await PersonChars.gender.set()


@dp.callback_query_handler(state='*', text='lookup_data')
async def get_data(callback: types.CallbackQuery):
    user = await dal.User.select_attributes(callback.from_user.id)
    if user.attempts >= 2:
        logger.error('Превышено кол-во попыток на пересоздание расписания')
        await callback.message.answer(
            'Количество попыток на создание расписания в тестовой версии ограничено 2 попытками,'
            ' пересоздать расписание невозможно'
        )
        return None

    await dal.User.increase_attempts_by_user_id(callback.from_user.id)

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


@dp.callback_query_handler(state=PersonChars.gender)
async def add_sex(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'gender_man':
        async with state.proxy() as data:
            data['gender'] = 'Мужской'
    if callback.data == 'gender_woman':
        async with state.proxy() as data:
            data['gender'] = 'Женский'

    await callback.message.answer('Укажите ваш возраст, сколько полных лет (введите число)')
    await PersonChars.age.set()


@dp.message_handler(state=PersonChars.age)
async def add_age(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['age'] = int(message.text)

    await message.answer(
        'Укажите ваш рост (введите число в см)'
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
        'Укажите ваш вес (введите число в кг)'
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
        'Есть ли у вас опыт занятий в спортивном зале? Если да, то сколько вы занимаетесь (напишите в свободной форме)'
    )
    await PersonChars.gym_experience.set()


@dp.message_handler(state=PersonChars.gym_experience)
async def add_illnesses(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gym_experience'] = message.text

    await message.answer(
        'Какая у вас цель занятий?'
    )
    await PersonChars.goal.set()


@dp.message_handler(state=PersonChars.goal)
async def add_drugs(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['goal'] = message.text

    await message.answer(
        'Через сколько недель вы хотите достичь своей цели (напишите числовое значение)?'
    )
    await PersonChars.time_to_reach.set()


@dp.message_handler(state=PersonChars.time_to_reach)
async def add_level_of_fitness(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['time_to_reach'] = int(message.text)

    await message.answer(
        'Насколько высокую интенсивность вы хотите видеть в тренировках?', reply_markup=kb.intensity
    )
    await PersonChars.intensity.set()


@dp.callback_query_handler(state=PersonChars.intensity)
async def add_goal(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'low':
        async with state.proxy() as data:
            data['intensity'] = 'low'
    if callback.data == 'moderate':
        async with state.proxy() as data:
            data['intensity'] = 'moderate'
    if callback.data == 'high':
        async with state.proxy() as data:
            data['intensity'] = 'high'

    await callback.message.answer(
        f'Сколько дней в неделю вы готовы уделять тренировкам (напишите численное значение)?'
    )

    await PersonChars.times_per_week.set()


@dp.message_handler(state=PersonChars.times_per_week)
async def add_goal(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    elif int(message.text) > 7:
        await message.answer('Необходимо ввести значение меньшее или равное 7')
    else:
        async with state.proxy() as data:
            data['times_per_week'] = int(message.text)

    await message.answer(
        'Есть ли у вас ограничения по здоровью (напишите в свободной форме)?'
    )
    await PersonChars.health_restrictions.set()


@dp.message_handler(state=PersonChars.health_restrictions)
async def add_goal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['health_restrictions'] = message.text

    await message.answer(
        'Введите свои нынешние результаты в присяде. Если нет - напишите нет'
    )

    await PersonChars.squats_results.set()


@dp.message_handler(state=PersonChars.squats_results)
async def add_result(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['squats_results'] = message.text

    await message.answer(
        'Введите свои нынешние результаты в жиме лежа. Если нет - напишите нет'
    )

    await PersonChars.bench_results.set()


@dp.message_handler(state=PersonChars.bench_results)
async def add_allergy(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['bench_results'] = message.text

    await message.answer(
        'Введите свои нынешние результаты в становой тяге. Если нет - напишите нет'
    )

    await PersonChars.deadlift_results.set()


@dp.message_handler(state=PersonChars.deadlift_results)
async def add_diet(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['deadlift_results'] = message.text

        await dal.User.add_attributes(state, message.from_user.id)
        await state.finish()

        await message.answer(
            'Ваши данные были внесены в базу, наш искусственный интеллект составляет вам расписание \n'
            'Подождите около 4 минут'
        )

        for attempt_number in range(3):
            try:
                timetable = await process_prompt(
                    user_id=message.from_user.id
                )
                await message.answer(
                    f'Вот ваше расписание на понедельник:\n{timetable.monday}',
                    reply_markup=kb.timetable
                )
                break
            except Exception as exc:
                logger.error(f'При обработке промпта произошла ошибка - {exc}. Попытка {attempt_number + 1}')
                if attempt_number == 2:
                    await message.answer(
                        'При создании расписания произошла ошибка'
                    )


### ВЕРСИЯ ЧАТА С ДООБУЧЕНИЕМ

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
        await message.reply('Сейчас..')
        logger.info(f'Сообщение - {message.text}')
        reply = ChatGPT().chat(message.text)
        logger.info(f'Ответ - {reply}')
        await message.reply(reply)
    except Exception as exc:
        logger.info(f'Ошибка - {exc}')
        await message.reply(f'При генерации ответа произошла ошибка - {exc}')
