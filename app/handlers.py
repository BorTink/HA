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

import dal
from utils import process_prompt, process_prompt_next_week, split_workout, process_workout, get_training_markup, \
    proccess_meal_plan_prompt
from app import keyboards as kb
from gpt.chat import ChatGPT
from .states import PersonChars, BaseStates, Admin

# ----- СТАРТ И ПОДПИСКА ---------

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
storage = RedisStorage2('localhost', 6379, db=5, pool_size=10, prefix='my_fsm_key')
dp = Dispatcher(bot=bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

PRICE = types.LabeledPrice(label='Подписка на 1 месяц', amount=399 * 100)


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message, state: FSMContext):
    if state:
        await state.finish()

    await dal.Starts.update_starts(message.from_user.id)
    logger.info('start')
    user = await dal.User.select_attributes(message.from_user.id)
    trainings, day, active = await dal.Trainings.get_trainings_by_day(message.from_user.id, 1)
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
                '- 👋 Добро пожаловать\n'
                'Я — виртуальный тренер Health AI.\n\n'
                '🎯 Составлю вам индивидуальный и наиболее эффективный для вас план тренировок '
                'и питания с траекторией развития на 9 недель;\n\n'
                'Приступая к тренировкам, вы подтверждаете, что ознакомились с информацией на '
                '<a href="https://health-ai.ru/ai">нашем сайте</a>.',
                reply_markup=kb.main_new,
                parse_mode='HTML'
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
    await asyncio.sleep(1.5)
    await message.answer(
        '🌟 Если вы не хотите стоять на месте и для вас важен прогресс в тренировках, '
        'рекомендуем оформить ежемесячную подписку!'
    )
    await asyncio.sleep(1.5)
    await message.answer(
        '📈 Так вы сможете соразмерно увеличивать нагрузки и менять программу занятий '
        'для получения максимальной пользы.'
    )
    await asyncio.sleep(1.5)
    await message.answer("Основные преимущества подписки:\n"
                         "▫️Регулярное обновление программы тренировок;\n"
                         "▫️Высокая персонализация (с опорой на ваши результаты);\n"
                         "▫️Повышенная эффективность от тренировок;\n"
                         "▫️Возможность обновлять свои данные;\n"
                         "▫️Поддержка на всём периоде занятий")
    await asyncio.sleep(1.5)
    await message.answer('Стоимость подписки 399 руб/мес.')
    await asyncio.sleep(1.5)
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
async def successful_payment(message: types.Message, state: FSMContext):
    logger.info(f'Оплата у пользователя {message.from_user.id} прошла успешно')
    await dal.User.update_subscribed_parameter(message.from_user.id, 1)
    await message.answer(f'Спасибо за покупку подписки!')

    await state.set_state(BaseStates.end_of_week_changes)
    temp_message = await message.answer('Перед составлением тренировок на следующую неделю, '
                                        'напишите коррективы, которые вы бы хотели внести '
                                        'в тренировки в целом '
                                        '(до 100 символов)')
    async with state.proxy() as data:
        data['temp_message'] = temp_message.message_id


@dp.message_handler(state='*', text='Вернуться в главное меню')
async def back_to_menu(message: types.Message, state: FSMContext):
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
    await state.set_state(BaseStates.start_workout)
    training, day = await dal.Trainings.get_active_training_by_user_id(callback.from_user.id)
    subscribed = await dal.User.check_if_subscribed_by_user_id(callback.from_user.id)
    if training:
        async with state.proxy() as data:
            data['day'] = day
            data['workout'] = training

        await callback.message.edit_text(
            f'<b>День {day}</b>\n' + f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' + training,
            reply_markup=kb.insert_weights_in_workout,
            parse_mode='HTML'
        )

    elif not subscribed:
        await state.set_state(BaseStates.end_of_trial)
        await callback.message.edit_text('Пробный период подошёл к концу.')
        await asyncio.sleep(1.5)
        await callback.message.answer(
            'Если вы хотите продолжить заниматься по персональной адаптивной программе, '
            'оформите ежемесячную подписку. С ней у вас будет доступ к новым тренировкам, '
            'возможность и дальше отслеживать свой прогресс и многое другое.'
        )
        await asyncio.sleep(1.5)
        await callback.message.answer('Стоимость подписки 399 руб/мес.')
        await asyncio.sleep(1.5)
        await callback.message.answer(
            'Оформляйте подписку на Health AI и меняйтесь к лучшему каждый день!',
            reply_markup=kb.subscribe_proposition
        )
    else:
        await state.set_state(BaseStates.end_of_week_changes)
        await callback.message.edit_text(
            'Вы закончили эту неделю тренировкок! '
            'Перед составлением тренировок на следующую неделю, '
            'напишите коррективы, которые вы бы хотели внести в тренировки в целом '
            '(до 100 символов)',
        )


@dp.callback_query_handler(state=BaseStates.end_of_trial, text='subscribe_later')
async def back_to_menu(message: types.Message, state: FSMContext):
    if state:
        await state.finish()

    await message.answer(
        'Выберите действие',
        reply_markup=kb.main
    )


@dp.callback_query_handler(state='*', text=['next_workout', 'prev_workout'])
async def switch_days(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:

        await state.set_state(BaseStates.show_trainings)
        if callback.data == 'next_workout':
            training, new_day, active = await dal.Trainings.get_next_training(
                user_id=callback.from_user.id,
                current_day=data['day']
            )
            if training:
                data['day'] = new_day
                data['workout'] = training

            else:
                training, new_day, active = await dal.Trainings.get_trainings_by_day(
                    user_id=callback.from_user.id,
                    day=1
                )
                data['day'] = 1
                data['workout'] = training

        elif callback.data == 'prev_workout':
            training, new_day, active = await dal.Trainings.get_prev_training(
                user_id=callback.from_user.id,
                current_day=data['day']
            )
            if training:
                data['day'] = new_day
                data['workout'] = training

            else:
                training, new_day, active = await dal.Trainings.get_prev_training(
                    user_id=callback.from_user.id,
                    current_day=1000000
                )
                data['day'] = new_day
                data['workout'] = training

        reply_markup = await get_training_markup(callback.from_user.id, data['day'])
        await callback.message.edit_text(
            f'<b>День {data["day"]}</b>\n' + (f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' if active else '') + training,
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
        '⏳ Подождите около 2-х минут, ии-тренер составляет вам персональную тренировку.'
    )

    await state.set_state(BaseStates.show_trainings)

    await dal.User.update_rebuilt_parameter(message.from_user.id)

    attempts = 0
    while attempts < 3:
        try:
            await process_prompt_next_week(
                user_id=message.from_user.id,
                client_edits_next_week=message.text
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

    training, new_day, active = await dal.Trainings.get_trainings_by_day(
        user_id=message.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await message.answer(
        '💡Если нажать на выделенные слова, вы перийдете на сайт с инструкцией к упражнению'
    )

    await message.answer(
        f'<b>День {data["day"]}</b>\n' + (f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' if active else '') + training,
        reply_markup=kb.trainings_tab,
        parse_mode='HTML'
    )


@dp.callback_query_handler(state=BaseStates.show_trainings, text='start_workout')
async def prestart_workout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        '☝️ Помните, что указанный в упражнениях вес является приблизительным. '
        'Если вам тяжело или легко выполнять заданное количество упражнений с каким-то весом, '
        'поменяйте его исходя из ваших возможностей.',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await asyncio.sleep(1.5)
    await callback.message.answer(
        'При возникновении любых проблем обязательно проконсультируйтесь с лицензированным специалистом!'
    )
    await asyncio.sleep(1.5)
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
    training, new_day, active = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    async with state.proxy() as data:
        data['day'] = 1
        data['workout'] = training

    await state.set_state(BaseStates.show_trainings)

    await callback.message.answer('Возвращаемся к тренировкам', reply_markup=kb.always_markup)
    await asyncio.sleep(1.5)

    await callback.message.answer(
        f'<b>День {data["day"]}</b>\n' + (f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' if active else '') + training,
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
            f'<b>День {data["day"]}</b>\n' + f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' + workout_in_process,
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
    training, new_day, active = await dal.Trainings.get_trainings_by_day(
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
    await asyncio.sleep(1.5)

    await state.set_state(BaseStates.show_trainings)
    await callback.message.answer(
        f'<b>День {data["day"]}</b>\n' + (f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' if active else '') + training,
        reply_markup=kb.trainings_tab,
        parse_mode='HTML'
    )


@dp.message_handler(state=BaseStates.end_of_week_changes)
async def get_end_of_week_changes_from_user(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) > 100:
            await bot.delete_message(message.chat.id, message.message_id)
            temp_message = await bot.edit_message_text('Ваши коррективы на тренировки должны быть меньше 100 символов',
                                                       message.chat.id, data['temp_message'])
            data['temp_message'] = temp_message.message_id
        else:
            await message.answer('⏳Ваши правки будут учтены, создаются тренировки на следующую неделю')
            attempts = 0
            while attempts < 3:
                try:
                    await process_prompt_next_week(
                        user_id=message.from_user.id
                    )
                    break
                except Exception as exc:
                    logger.error(f'При отправке и обработке промпта произошла ошибка - {exc}')
                    attempts += 1

            await dal.User.increase_week_parameter(message.from_user.id)

            await dal.Trainings.update_active_training_by_day(
                user_id=message.from_user.id,
                day=1,
                active=True
            )
            training, new_day, active = await dal.Trainings.get_trainings_by_day(
                user_id=message.from_user.id,
                day=1
            )
            async with state.proxy() as data:
                data['day'] = 1
                data['workout'] = training

            await message.answer(
                '✅ План ваших тренировок готов! Попробуйте их выполнить и возвращайтесь с обратной связью!',
                reply_markup=kb.always_markup
            )
            await asyncio.sleep(2)
            await message.answer(
                f'<b>День {data["day"]}</b>\n' + (f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' if active else '') + training,
                reply_markup=kb.trainings_tab,
                parse_mode='HTML'
            )


@dp.callback_query_handler(state=[BaseStates.show_trainings, BaseStates.end_of_trial], text='get_subscription')
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
    await callback.message.answer('Возвращаемся в главное меню', reply_markup=kb.always_markup)
    await asyncio.sleep(1.5)

    if callback.message.from_user.id in [635237071, 284863184]:
        await callback.message.answer('ЭТО АДМИН ПАНЕЛЬ', reply_markup=kb.always_markup)
        await callback.message.answer('Выберите действие',
                                      reply_markup=kb.main_admin)
    else:
        await callback.message.answer('Здравствуйте!', reply_markup=kb.always_markup)
        await callback.message.answer('Выберите действие',
                                      reply_markup=kb.main)


@dp.callback_query_handler(state=[BaseStates.start_workout, BaseStates.add_weight], text=['no', 'return_to_training'])
async def do_not_leave_workout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(BaseStates.start_workout)


@dp.callback_query_handler(state=[BaseStates.start_workout, BaseStates.add_weight], text='meal_plan')
async def go_to_meal_plan(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BaseStates.meals)
    async with state.proxy() as data:
        try:
            await bot.delete_message(callback.message.chat.id, data['temp_message'])
        except:
            pass

    meals = await dal.Meals.get_all_meals_by_user_id(callback.from_user.id)
    if meals:
        meal_plan = meals[0].meal_plan
        await callback.message.edit_text(
            meal_plan,
            reply_markup=kb.meal_plan,
            parse_mode='HTML'
        )
    else:
        await callback.message.edit_text(
            '⏳Ваш план питания составляется, подождите (не более 2х минут)…'
        )

        meal_plan = await proccess_meal_plan_prompt(callback.from_user.id)

        await callback.message.edit_text(
            '🍏 Ваш план питания составлен! \n\n'
            'Старайтесь следовать инструкциям!'
        )

        await callback.message.edit_text(
            meal_plan,
            reply_markup=kb.meal_plan,
            parse_mode='HTML'
        )


@dp.callback_query_handler(state=BaseStates.meals, text='go_to_workout')
async def go_to_workout(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await state.set_state(BaseStates.start_workout)

        data['message'] = callback.message.message_id
        data['workout'], data['day'] = await dal.Trainings.get_active_training_by_user_id(callback.from_user.id)
        data['workout'] = data['workout'].split(' кг')

        if 'weight_index' not in data.keys():
            data['weight_index'] = 0

        current_weight = data['workout'][data['weight_index']].split(' ')[-1]
        workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)

        await process_workout(
            workout_in_process,
            data,
            state,
            callback.message,
            kb,
            user_id=callback.from_user.id,
            return_to_training=True
        )


# ----- АНКЕТА ПОЛЬЗОВАТЕЛЯ ---------


@dp.callback_query_handler(state='*', text=['update_data', 'insert_data'])
async def create_edit(callback: types.CallbackQuery):
    await asyncio.sleep(1.5)
    await callback.message.answer(
        '- 🏃🏽 Пробный период начался!\n'
        'Сейчас вам доступно:\n'
        '- 1 тренировка с возможностью пересборки на ваших комментариях (если вам что-то не понравится);\n\n'
        '- Внесение своих показателей тренировки и просмотр тренировки 7-й недели;\n\n'
        '- Просмотр вашей персональной траектории развития на 9 недель;\n\n'
        '- План питания на день в соответствии с вашими целями;',
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
    await callback.message.answer(
        '💬 Осталось ответить на *вопросы* и ваш план тренировок будет готов!',
        parse_mode='Markdown'
    )
    await asyncio.sleep(1.5)
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
async def add_allergy_products(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['health_restrictions'] = message.text

        await message.delete()
        await bot.edit_message_text(
            'Есть ли у вас продукты, на которых у вас аллергия или которые избегаете? (Напишите до 100 символов)',
            chat_id=message.chat.id,
            message_id=data['info_message']
        )

        await PersonChars.allergy.set()


@dp.message_handler(state=PersonChars.allergy)
async def add_intensity(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['allergy'] = message.text

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

    await dal.User.add_attributes(state, callback.from_user.id)
    await state.set_state(BaseStates.start_workout)

    await callback.message.edit_text(
        '⏳ Подождите около 2-х минут, ии-тренер составляет вам персональную тренировку.'
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
    training, new_day, active = await dal.Trainings.get_trainings_by_day(
        user_id=callback.from_user.id,
        day=1
    )
    if training is None:
        await callback.message.answer('При создании тренировки произошла ошибка')

    async with state.proxy() as data:
        data['day'] = 1
        data['weight_index'] = 0
        data['workout'] = training.split(' кг')

    await callback.message.answer(
        '✅ Ваша первая тренировка составлена!\n' 
        '(вы можете ее пересобрать при необходимости)\n\n\n'
        '💡Если нажать на выделенные слова, вы перийдете на сайт с инструкцией к упражнению;\n\n\n'
        '• введите подходящий вес, нажав кнопку «ввести вес», для каждого упражнения, чтобы улучшить тренировки;\n\n\n'    
        '🚀 Удачной тренировки, вы достигните своих целей!\n'
    )
    await asyncio.sleep(3)
    await callback.message.answer(
        '🏁 Чтобы завершить тренировку, нажмите ввести вес, если вес не подошел, либо завершить тренировку.',
        reply_markup=kb.always_markup
    )
    await asyncio.sleep(2)

    await dal.Trainings.update_in_progress_training_by_day(
        user_id=callback.from_user.id,
        day=data['day'],
        in_progress=True
    )

    current_weight = data['workout'][0].split(' ')[-1]
    workout_in_process = await split_workout(data['workout'], data['weight_index'], current_weight)
    await callback.message.answer(
        f'<b>День {data["day"]}</b>\n' + f'<b>(АКТИВНАЯ ТРЕНИРОВКА)</b>\n' + workout_in_process,
        reply_markup=kb.insert_weights_in_workout,
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
