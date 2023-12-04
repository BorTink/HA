import asyncio
import os
import pathlib

import tiktoken
from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types.message import ContentType

from dotenv import load_dotenv
from loguru import logger

from utils import process_prompt, split_workout, process_workout, get_training_markup
from .states import PersonChars, BaseStates, Admin
from app import keyboards as kb
import dal
from gpt.chat import ChatGPT

# ----- СТАРТ И ПОДПИСКА ---------

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
storage = RedisStorage2('localhost', 6379, db=5, pool_size=10, prefix='my_fsm_key')
dp = Dispatcher(bot=bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

PRICE = types.LabeledPrice(label='Подписка на 1 месяц', amount=399*100)


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message, state: FSMContext):
    if state:
        await state.finish()

    await dal.Starts.update_starts(message.from_user.id)
    logger.info('start')
    user = await dal.User.select_attributes(message.from_user.id)
    trainings, day = await dal.Trainings.get_trainings_by_day(message.from_user.id, 1)
    logger.info(f'user - {user}')
    async with state.proxy() as data:
        if user and trainings:
            if message.from_user.id in [635237071, 284863184]:
                await message.answer('ЭТО АДМИН ПАНЕЛЬ', reply_markup=kb.always_markup)
                await message.answer('Выберите действие',
                                     reply_markup=kb.main_admin)
            else:
                await message.answer('Здравствуйте!', reply_markup=kb.always_markup)
                await message.answer('Выберите действие',
                                     reply_markup=kb.main)
        else:
            await message.answer(
                '👋 Добро пожаловать! Я виртуальный тренер Health AI. Помогу составить сбалансированные планы тренировок '
                'под ваши индивидуальные запросы.',
                parse_mode='Markdown'
            )
            await asyncio.sleep(1)
            await message.answer(
                '💪 С моей помощью вы сможете разработать эффективную программу занятий и легко отслеживать свой прогресс.',
                parse_mode='Markdown'
            )
            await asyncio.sleep(1)
            await message.answer(
                '_Тренировки, разработанные Health AI, основаны на научных работах и советах профессиональных тренеров, '
                'но несут исключительно рекомендательный характер._',
                parse_mode='Markdown'
            )
            await asyncio.sleep(1)
            await message.answer(
                '_Мы не несём ответственности за травмы, которые могут быть получены в процессе выполнения упражнений._',
                reply_markup=kb.main_new,
                parse_mode='Markdown'
            )


@dp.callback_query_handler(state='*', text='ADMIN_go_to_assistant_testing')
async def go_to_assistant_training(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Admin.assistant_training)
    global this_gpt
    this_gpt = ChatGPT()
    await this_gpt.create_thread()
    await callback.message.edit_text('Вы перешли в раздел тестирования ассистента.')
    await asyncio.sleep(0.5)
    await callback.message.answer('Для перезагрузки ассистента напишите */start* и зайдите сюда заново',
                                  parse_mode='Markdown')
    await asyncio.sleep(0.5)
    await callback.message.answer('Можете писать сообщения')


@dp.message_handler(state=Admin.assistant_training)
async def assistant_message(message: types.Message, state: FSMContext):
    await this_gpt.add_message(message.text)
    status = await this_gpt.create_run()

    while status.status != 'completed':
        status = await this_gpt.get_run_status()
        await asyncio.sleep(5)

    messages = await this_gpt.get_all_messages()
    await message.answer(messages.data[0].content[0].text.value)


# @dp.callback_query_handler(state='*', text='generate_trainings')
# async def generate_trainings(callback: types.CallbackQuery, state: FSMContext):
#     temp_message = await callback.message.answer(
#         '⏳Подождите, составляем персональную тренировку'
#     )
#
#     await state.set_state(BaseStates.show_trainings)
#
#     await process_prompt(
#         user_id=callback.from_user.id
#     )
#
#     await dal.Trainings.update_active_training_by_day(
#         user_id=callback.from_user.id,
#         day=1,
#         active=True
#     )
#
#     training, new_day = await dal.Trainings.get_trainings_by_day(
#         user_id=callback.from_user.id,
#         day=1
#     )
#     async with state.proxy() as data:
#         data['day'] = 1
#         data['workout'] = training
#
#     await temp_message.edit_text(
#         '✅ План вашей первой тренировки готов! Попробуйте его выполнить и возвращайтесь с обратной связью!'
#     )
#     await asyncio.sleep(2)
#     await callback.message.answer(
#         training,
#         reply_markup=kb.trainings_tab
#     )


@dp.message_handler(state='*', text='Купить подписку')
async def buy_subscription(message: types.Message, state: FSMContext):

    with open(str(pathlib.Path(__file__).parent.parent) + '/img/logo.jpg', 'rb') as photo_file:
        await bot.send_photo(chat_id=message.from_user.id, photo=photo_file)
    await asyncio.sleep(1)
    await message.answer(
        '🌟 Если вы не хотите стоять на месте и для вас важен прогресс в тренировках, '
        'рекомендуем оформить ежемесячную подписку!'
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
        'Оформляйте подписку на Health AI и меняйтесь к лучшему каждый день!'
    )
    await asyncio.sleep(2)

    if os.getenv('PAYMENTS_TOKEN').split(':')[1] == 'TEST':
        await bot.send_invoice(message.chat.id,
                               title='Месячная подписка на сервис HealthAI',
                               description='Месячная подписка на сервис HealthAI',
                               provider_token=os.getenv('PAYMENTS_TOKEN'),
                               provider_data={
                                   "receipt": {
                                       "items": [
                                           {
                                               "description": "Месячная подписка на сервис HealthAI",
                                               "quantity": "1",
                                               "amount": {"value": "399.00", "currency": "RUB"},
                                               "vat_code": 1
                                           }
                                       ],
                                       "customer": {"email": "borisus.amusov@mail.ru"}
                                   }
                               },
                               currency='rub',
                               photo_url='/home/boris/TelegramBots/Health_AI/img/logo.jpg',
                               photo_width=1270,
                               is_flexible=False,
                               prices=[PRICE],
                               start_parameter='one-month-subscription',
                               payload='test-invoice-payload')
    else:
        await bot.send_invoice(message.chat.id,
                               title='Месячная подписка на сервис HealthAI',
                               description='Месячная подписка на сервис HealthAI',
                               provider_token=os.getenv('PAYMENTS_TOKEN'),
                               provider_data={
                                   "receipt": {
                                       "items": [
                                           {
                                               "description": "Месячная подписка на сервис HealthAI",
                                               "quantity": "1",
                                               "amount": {"value": "399.00", "currency": "RUB"},
                                               "vat_code": 1
                                           }
                                       ],
                                       "customer": {"email": "borisus.amusov@mail.ru"}
                                   }
                               },
                               currency='rub',
                               photo_url='/home/boris/TelegramBots/Health_AI/img/logo.jpg',
                               photo_width=1270,
                               is_flexible=False,
                               prices=[PRICE],
                               start_parameter='one-month-subscription',
                               payload='subscription-payload')


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True, error_message='Произошла ошибка')


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    logger.info(f'Оплата у пользователя {message.from_user.id} прошла успешно')
    await dal.User.update_subscribed_parameter(message.from_user.id, 1)
    await message.answer(f'Спасибо за покупку подписки! Ждем тебя на следующей тренировке!')


@dp.message_handler(state='*', text='Вернуться в главное меню')
async def back_to_menu(message: types.Message, state: FSMContext):
    await dal.User.update_chat_id_parameter(message.from_user.id, message.chat.id)
    if state:
        await state.finish()

    await message.answer(
        'Выберите действие',
        reply_markup=kb.main
    )


@dp.message_handler(state='*', text='Техподдержка / Оставить отзыв')
async def support(message: types.Message, state: FSMContext):
    await state.set_state(BaseStates.support)

    await message.answer(
        'Техподдержка или оставить отзыв?',
        reply_markup=kb.support
    )


@dp.callback_query_handler(state=BaseStates.support, text='tech_support')
async def tech_support(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Со всеми вопросами пишите сюда https://t.me/sergey_akhapkin1703')

    await state.finish()

    await callback.message.answer(
        'Выберите действие',
        reply_markup=kb.main
    )


@dp.callback_query_handler(state=BaseStates.support, text='add_review')
async def add_review(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BaseStates.add_review)
    await callback.message.edit_text('Напишите в следующем сообщении свой отзыв')


@dp.message_handler(state=BaseStates.add_review)
async def write_review(message: types.Message, state: FSMContext):
    await dal.Reviews.add_review(message.from_user.id, message.text)

    await message.answer('Спасибо за ваш отзыв!')
    await state.finish()

    await message.answer(
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

    if training:
        async with state.proxy() as data:
            data['day'] = 1
            data['workout'] = training

        await callback.message.edit_text(
            f'День {day}\n' + training,
            reply_markup=kb.trainings_tab_without_prev,
            parse_mode='HTML'
        )

    else:
        await callback.message.edit_text(
            f"У вас нет доступных тренировок",
            reply_markup=kb.main
        )


@dp.callback_query_handler(state='*', text=['next_workout', 'prev_workout'])
async def switch_days(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await dal.User.update_chat_id_parameter(callback.from_user.id, callback.message.chat.id)
        if callback.data == 'next_workout':
            training, new_day = await dal.Trainings.get_next_training(
                user_id=callback.from_user.id,
                current_day=data['day']
            )
            if training:
                data['day'] = new_day
                data['workout'] = training

            else:
                training, new_day = await dal.Trainings.get_trainings_by_day(
                    user_id=callback.from_user.id,
                    day=1
                )
                data['day'] = 1
                data['workout'] = training

        elif callback.data == 'prev_workout':
            training, new_day = await dal.Trainings.get_prev_training(
                user_id=callback.from_user.id,
                current_day=data['day']
            )
            if training:
                data['day'] = new_day
                data['workout'] = training

            else:
                training, new_day = await dal.Trainings.get_prev_training(
                    user_id=callback.from_user.id,
                    current_day=1000000
                )
                data['day'] = new_day
                data['workout'] = training

        reply_markup = await get_training_markup(callback.from_user.id, data['day'])
        await callback.message.edit_text(
            f'День {data["day"]}\n' + training,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


@dp.callback_query_handler(state=BaseStates.show_trainings, text='rebuild_workouts')
async def ask_client_for_changes(callback: types.CallbackQuery, state: FSMContext):
    user = await dal.User.select_attributes(callback.from_user.id)
    if callback.from_user.id == 913925619:
        if user.rebuilt > 31:
            await callback.answer(
                'Вы уже 30 раз пересобрали тренировку на неделю'
            )
        else:
            await callback.message.answer(
                'Введите что вы хотите изменить до 100 символов. '
                '(Тренировку можно пересобрать 1 раз в пробной версии, может добавить нужные упражнения или что-то убрать)'
            )
            await state.set_state(BaseStates.rebuild_workouts)
    elif user.rebuilt == 1:
        await callback.answer(
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

    attempts = 0
    while attempts < 3:
        try:
            await process_prompt(
                user_id=message.from_user.id
            )
            break
        except Exception as exc:
            logger.error(f'При отправке и обработке промпта произошла ошибка - {exc}')
            attempts += 1

    await dal.Trainings.update_active_training_by_day(
        user_id=message.from_user.id,
        day=1,
        active=True
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
        reply_markup=kb.trainings_tab,
        parse_mode='HTML'
    )


@dp.callback_query_handler(state=BaseStates.show_trainings, text='start_workout')
async def prestart_workout(callback: types.CallbackQuery, state: FSMContext):
    await dal.User.update_chat_id_parameter(callback.from_user.id, callback.message.chat.id)
    await callback.message.answer(
        '☝️ Помните, что указанный в упражнениях вес является приблизительным. '
        'Если вам тяжело или легко выполнять заданное количество упражнений с каким-то весом, '
        'поменяйте его исходя из ваших возможностей.',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await asyncio.sleep(1)
    await callback.message.answer(
        'При возникновении любых проблем обязательно проконсультируйтесь с лицензированным специалистом!'
    )
    await asyncio.sleep(1)
    await state.set_state(BaseStates.start_workout)
    async with state.proxy() as data:
        data['weight_index'] = 0
        data['workout'], data['day'] = await dal.Trainings.get_active_training_by_user_id(callback.from_user.id)
        data['workout'] = data['workout'].split(' кг')
    await callback.message.answer(
        '☝После того, как пройдете тренировку (или по ходу выполнения упражнений), '
        'обязательно введите свои показатели, чтобы усовершенствовать будущие занятия. '
        'Это поможет при расчёте оптимальных нагрузок и времени восстановления.\nХорошей тренировки!',
        reply_markup=kb.start_workout
    )


@dp.callback_query_handler(state=BaseStates.start_workout, text='go_back')
async def go_back_to_trainings(callback: types.CallbackQuery, state: FSMContext):
    training, new_day = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await state.set_state(BaseStates.show_trainings)

    await callback.message.answer('Возвращаемся к тренировкам', reply_markup=kb.always_markup)
    await asyncio.sleep(1)

    await callback.message.answer(
        training,
        reply_markup=kb.trainings_tab,
        parse_mode='HTML'
    )


@dp.callback_query_handler(state=BaseStates.start_workout, text='insert_weights')
async def begin_workout(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await dal.Trainings.update_in_progress_training_by_day(
            user_id=callback.from_user.id,
            day=data['day'],
            in_progress=True
        )
        current_weight = data['workout'][0].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
        await callback.message.answer(
            f'День {data["day"]}\n' + workout_in_process,
            reply_markup=kb.insert_weights_in_workout,
            parse_mode='HTML'
        )


@dp.callback_query_handler(state=BaseStates.start_workout, text='add_weight')
async def add_weight(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = callback.message.message_id
        temp_message = await callback.message.answer(
            'Введите новый вес',
            reply_markup=kb.insert_weight
        )
        data['temp_message'] = temp_message.message_id
    await state.set_state(BaseStates.add_weight)


@dp.message_handler(state=BaseStates.add_weight)
async def add_weight(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['temp_message'])
            except Exception as exc:
                pass
            await message.delete()

            temp_message = await message.answer(
                'Необходимо ввести численное значение',
                reply_markup=kb.insert_weight)
            data['temp_message'] = temp_message.message_id

        elif int(message.text) > 300:
            try:
                await bot.delete_message(message.chat.id, data['temp_message'])
            except Exception as exc:
                pass
            await message.delete()

            temp_message = await message.answer(
                'Похоже вы опечатались, введите значение повторно',
                reply_markup=kb.insert_weight)
            data['temp_message'] = temp_message.message_id

        else:
            await message.delete()
            try:
                await bot.delete_message(message.chat.id, data['temp_message'])
            except Exception as exc:
                pass

            workout_in_process = await split_workout(data['workout'], data['weight_index'], int(message.text))
            await process_workout(workout_in_process, data, state, message, kb)


@dp.callback_query_handler(state=BaseStates.start_workout, text='skip_weight')
async def skip_weight(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = callback.message.message_id
        current_weight = data['workout'][data['weight_index']].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
        await process_workout(workout_in_process, data, state, callback.message, kb, user_id=callback.from_user.id)


@dp.callback_query_handler(state=BaseStates.start_workout, text='leave_workout')
async def ask_to_leave_workout(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = callback.message.message_id
    await callback.message.answer(f'Вы действительно хотите покинуть тренировку?', reply_markup=kb.leave_workout)


@dp.callback_query_handler(state=BaseStates.start_workout, text='yes')
async def leave_workout(callback: types.CallbackQuery, state: FSMContext):
    training, new_day = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        await dal.Trainings.update_in_progress_training_by_day(
            user_id=callback.from_user.id,
            day=data['day'],
            in_progress=False
        )
        data['day'] = 1
        data['workout'] = training

        try:
            await bot.delete_message(callback.message.chat.id, data['message'])
        except Exception as exc:
            pass
        await callback.message.delete()

    await callback.message.answer('Возвращаемся к тренировкам', reply_markup=kb.always_markup)
    await asyncio.sleep(1)

    await state.set_state(BaseStates.show_trainings)
    await callback.message.answer(
        training,
        reply_markup=kb.trainings_tab,
        parse_mode='HTML'
    )


@dp.callback_query_handler(state=BaseStates.show_trainings, text='get_subscription')
async def get_subscription(callback: types.CallbackQuery, state: FSMContext):
    if os.getenv('PAYMENTS_TOKEN').split(':')[1] == 'TEST':
        await bot.send_invoice(callback.message.chat.id,
                               title='Месячная подписка на сервис HealthAI',
                               description='Месячная подписка на сервис HealthAI',
                               provider_token=os.getenv('PAYMENTS_TOKEN'),
                               provider_data={
                                   "receipt": {
                                       "items": [
                                           {
                                               "description": "Месячная подписка на сервис HealthAI",
                                               "quantity": "1",
                                               "amount": {"value": "399.00", "currency": "RUB"},
                                               "vat_code": 1
                                           }
                                       ],
                                       "customer": {"email": "borisus.amusov@mail.ru"}
                                   }
                               },
                               currency='rub',
                               photo_url='/home/boris/TelegramBots/Health_AI/img/logo.jpg',
                               photo_width=1270,
                               is_flexible=False,
                               prices=[PRICE],
                               start_parameter='one-month-subscription',
                               payload='test-invoice-payload')
    else:
        await bot.send_invoice(callback.message.chat.id,
                               title='Месячная подписка на сервис HealthAI',
                               description='Месячная подписка на сервис HealthAI',
                               provider_token=os.getenv('PAYMENTS_TOKEN'),
                               provider_data={
                                   "receipt": {
                                       "items": [
                                           {
                                               "description": "Месячная подписка на сервис HealthAI",
                                               "quantity": "1",
                                               "amount": {"value": "399.00", "currency": "RUB"},
                                               "vat_code": 1
                                           }
                                       ],
                                       "customer": {"email": "borisus.amusov@mail.ru"}
                                   }
                               },
                               currency='rub',
                               photo_url='/home/boris/TelegramBots/Health_AI/img/logo.jpg',
                               photo_width=1270,
                               is_flexible=False,
                               prices=[PRICE],
                               start_parameter='one-month-subscription',
                               payload='subscription-payload')


@dp.callback_query_handler(state=BaseStates.show_trainings, text='subscribe_later')
async def subscribe_later(callback: types.CallbackQuery, state: FSMContext):
    training, day = await dal.Trainings.get_active_training_by_user_id(callback.from_user.id)

    async with state.proxy() as data:
        next_training_in_days = int(day) - int(data['day'])

        if next_training_in_days % 100 == 1:
            day_word = 'день'
        elif next_training_in_days % 100 in [2, 3, 4]:
            day_word = 'дня'
        else:
            day_word = 'дней'

        await callback.message.answer(f'Отличная работа! Так держать! '
                                      f'Следующая тренировка ждёт вас через {next_training_in_days} {day_word}.')
        await callback.message.answer('Возвращаемся к тренировкам', reply_markup=kb.always_markup)
        await asyncio.sleep(1.5)

        await callback.message.answer(
            f'День {data["day"]}\n' + data['workout'],
            reply_markup=kb.trainings_tab,
            parse_mode='HTML'
        )


@dp.callback_query_handler(state=[BaseStates.start_workout, BaseStates.add_weight], text=['no', 'return_to_training'])
async def do_not_leave_workout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(BaseStates.start_workout)


# ----- АНКЕТА ПОЛЬЗОВАТЕЛЯ ---------


@dp.callback_query_handler(state='*', text=['update_data', 'insert_data'])
async def create_edit(callback: types.CallbackQuery):
    await callback.message.answer(
        '🏃 Начинаем пробный период! Туда включён план тренировок на первую неделю и возможность 1 раз пересобрать его.'
    )
    await asyncio.sleep(1)
    await callback.message.answer(
        '➡️ После завершения пробного периода вам будет предложено оформить подписку '
        'для продолжения занятий и доступа к продвинутому функционалу.'
    )
    await asyncio.sleep(1)
    await callback.message.answer(
        """
       💬 Пожалуйста, пройдите небольшую анкету, чтобы я смог составить вам план персональных тренировок на эту неделю.
        """
    )
    await asyncio.sleep(1)
    await callback.message.answer(
        'Укажите свой пол',
        reply_markup=kb.gender
    )
    await PersonChars.gender.set()


@dp.callback_query_handler(state=PersonChars.gender)
async def add_sex(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if callback.data == 'gender_man':
            data['gender'] = 'Мужской'
        if callback.data == 'gender_woman':
            data['gender'] = 'Женский'

        info_message = await callback.message.edit_text('Введите свой возраст (Полных лет)')
        data['info_message'] = info_message.message_id
        await PersonChars.age.set()


@dp.message_handler(state=PersonChars.age)
async def add_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['info_message'])
            except Exception as exc:
                pass
            await message.delete()

            info_message = await message.answer('Необходимо ввести численное значение. '
                                                'Введите свой возраст (Полных лет)')
            data['info_message'] = info_message.message_id

        else:
            data['age'] = int(message.text)

            await message.delete()
            await bot.edit_message_text(
                'Укажите свой рост (см)',
                chat_id=message.chat.id,
                message_id=data['info_message']
            )
            await PersonChars.height.set()


@dp.message_handler(state=PersonChars.height)
async def add_height(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['info_message'])
            except Exception as exc:
                pass
            await message.delete()

            info_message = await message.answer('Необходимо ввести численное значение')
            data['info_message'] = info_message.message_id
        else:
            data['height'] = int(message.text)

            await message.delete()
            await bot.edit_message_text(
                'Введите свой вес (кг)',
                chat_id=message.chat.id,
                message_id=data['info_message']
            )
            await PersonChars.weight.set()


@dp.message_handler(state=PersonChars.weight)
async def add_weight(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['info_message'])
            except Exception as exc:
                pass
            await message.delete()

            info_message = await message.answer('Необходимо ввести численное значение')
            data['info_message'] = info_message.message_id
        else:
            data['weight'] = int(message.text)

            await message.delete()
            await bot.edit_message_text(
                'Оцените ваш уровень физической подготовки',
                chat_id=message.chat.id,
                message_id=data['info_message'],
                reply_markup=kb.gym_experience
            )
            await PersonChars.gym_experience.set()


@dp.callback_query_handler(state=PersonChars.gym_experience)
async def add_gym_experience(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['gym_experience'] = callback.data
    if callback.data in ['medium', 'experienced']:
        await callback.message.edit_text(
            'Знаете ли вы свои макимальные показатели веса в жиме лежа, становой тяге и приседаниях со штангой?',
            reply_markup=kb.max_results
        )
        await PersonChars.max_results.set()
    else:
        await callback.message.edit_text(
            'Каких результатов вы ожидаете от тренировок?',
            reply_markup=kb.expected_results
        )
        await PersonChars.goals.set()


@dp.callback_query_handler(state=PersonChars.max_results)
async def ask_max_results(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if callback.data == 'yes':
            info_message = await callback.message.edit_text(
                'Укажите максимальный вес в жиме лежа (Учитывая вес штанги 20 кг, указать в кг):'
            )
            data['info_message'] = info_message.message_id
            await PersonChars.bench_results.set()

        if callback.data == 'no':
            info_message = await callback.message.edit_text(
                'Каких результатов вы ожидаете от тренировок?',
                reply_markup=kb.expected_results
            )
            data['info_message'] = info_message.message_id
            await PersonChars.goals.set()


@dp.message_handler(state=PersonChars.bench_results)
async def add_bench_results(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['info_message'])
            except Exception as exc:
                pass
            await message.delete()

            info_message = await message.answer('Необходимо ввести численное значение')
            data['info_message'] = info_message.message_id
        else:
            data['bench_results'] = int(message.text)

            await message.delete()
            info_message = await bot.edit_message_text(
                'Укажите максимальный вес в становой тяге (Учитывая вес штанги 20 кг, указать в кг).',
                chat_id=message.chat.id,
                message_id=data['info_message']
            )
            data['info_message'] = info_message.message_id
            await PersonChars.deadlift_results.set()


@dp.message_handler(state=PersonChars.deadlift_results)
async def add_deadlift_results(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['info_message'])
            except Exception as exc:
                pass
            await message.delete()

            info_message = await message.answer('Необходимо ввести численное значение')
            data['info_message'] = info_message.message_id
        else:
            data['deadlift_results'] = int(message.text)

            await message.delete()
            info_message = await bot.edit_message_text(
                'Укажите максимальный вес в приседаниях со штангой (Учитывая вес штанги 20 кг, указать в кг).',
                chat_id=message.chat.id,
                message_id=data['info_message']
            )
            data['info_message'] = info_message.message_id
            await PersonChars.squats_results.set()


@dp.message_handler(state=PersonChars.squats_results)
async def add_squats_results(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() is False:
            try:
                await bot.delete_message(message.chat.id, data['info_message'])
            except Exception as exc:
                pass
            await message.delete()

            info_message = await message.answer('Необходимо ввести численное значение')
            data['info_message'] = info_message.message_id
        else:
            data['squats_results'] = int(message.text)

            await message.delete()
            await bot.edit_message_text(
                'Каких результатов вы ожидаете от тренировок?',
                chat_id=message.chat.id,
                message_id=data['info_message'],
                reply_markup=kb.expected_results
            )
            await PersonChars.goals.set()


@dp.callback_query_handler(state=PersonChars.goals)
async def add_goal(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['goals'] = callback.data

        info_message = await callback.message.edit_text(
            'Хотите ли вы прокачать какие-то отдельные части тела больше? Напишите до 100 символов'
        )
        data['info_message'] = info_message.message_id
        await PersonChars.focus.set()


@dp.message_handler(state=PersonChars.focus)
async def add_squats_results(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['goals'] += '. Additionally, ' + message.text

        await message.delete()
        await bot.edit_message_text(
            'Насколько интенсивно вы готовы заниматься? Укажите интенсивность тренировок.',
            chat_id=message.chat.id,
            message_id=data['info_message'],
            reply_markup=kb.intensity
        )
        await PersonChars.intensity.set()


@dp.callback_query_handler(state=PersonChars.intensity)
async def add_intensity(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['intensity'] = callback.data

        info_message = await callback.message.edit_text(
            'Есть ли у вас какие-нибудь противопоказания к тренировкам? Если да, то укажите какие '
            '(Например: травмы, растяжения, проблемы с позвоночником, высокое артериальное давление).'
            'Напишите до 100 символов.'
        )
        data['info_message'] = info_message.message_id
        await PersonChars.health_restrictions.set()


@dp.message_handler(state=PersonChars.health_restrictions)
async def add_intensity(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['health_restrictions'] = message.text

        await message.delete()
        await bot.edit_message_text(
            'Укажите одним числом сколько раз в неделю вы готовы заниматься. '
            '(Рекомендованное количество: 3-4 дня в неделю, ввести возможно от 2 до 4 дней)',
            chat_id=message.chat.id,
            message_id=data['info_message'],
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

    await dal.User.add_attributes(state, callback.from_user.id, callback.message.chat.id)
    await state.set_state(BaseStates.show_trainings)

    await callback.message.edit_text(
        '⏳Подождите, составляем персональную тренировку'
    )

    attempts = 0
    while attempts < 3:
        try:
            await process_prompt(
                user_id=callback.from_user.id
            )
            break
        except Exception as exc:
            logger.error(f'При отправке и обработке промпта произошла ошибка - {exc}')
            attempts += 1

    await dal.Trainings.update_active_training_by_day(
        user_id=callback.from_user.id,
        day=1,
        active=True
    )
    training, new_day = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await callback.message.answer(
        '✅ План вашей первой тренировки готов! Попробуйте его выполнить и возвращайтесь с обратной связью!',
        reply_markup=kb.always_markup
    )
    await asyncio.sleep(2)
    await callback.message.answer(
        training,
        reply_markup=kb.trainings_tab,
        parse_mode='HTML'
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


# @dp.message_handler(state=None)
# async def answer(message: types.Message):
#     try:
#         encoding = tiktoken.get_encoding('cl100k_base')
#         prompt_num_tokens = len(encoding.encode(message.text))
#         logger.info(f'Сообщение от user_id {message.from_user.id} - {message.text}')
#
#         logger.info(f'Длина промпта для расписания '
#                     f'- {prompt_num_tokens} токенов')
#         await message.reply(f'Длина промпта для расписания '
#                     f'- {prompt_num_tokens} токенов')
#
#         reply = await ChatGPT().chat(message.text)
#         reply_num_tokens = len(encoding.encode(reply))
#         await message.answer(f'Длина ответа '
#                     f'- {reply_num_tokens} токенов. '
#                     f'В сумме вышло {prompt_num_tokens + reply_num_tokens} токенов')
#
#         logger.info(f'Длина ответа '
#                     f'- {reply_num_tokens} токенов. '
#                     f'В сумме вышло {prompt_num_tokens + reply_num_tokens} токенов')
#
#         logger.info(f'Ответ - {reply}')
#         await message.reply(reply)
#     except Exception as exc:
#         logger.info(f'Ошибка - {exc}')
#         await message.reply(f'При генерации ответа произошла ошибка - {exc}')
