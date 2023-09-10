import time
from time import sleep
import os

from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from dotenv import load_dotenv
from loguru import logger

from .states import PersonChars, TimetableDays
from app import keyboards as kb
from gpt.chat import fill_prompt
import dal

load_dotenv()
bot = Bot(os.getenv('TOKEN'))

dp = Dispatcher(bot=bot, storage=MemoryStorage())  # storage впоследствии изменить на redis
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message, state: FSMContext):
    if state:
        await state.finish()

    user = await dal.User.select_attributes(message.from_user.id)
    if user:
        await message.answer('Выберите действие', reply_markup=kb.main)
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


@dp.callback_query_handler(state=None, text=['update_data', 'insert_data'])
async def create_edit(callback: types.CallbackQuery):
    await callback.message.answer(
        'Укажите ваш пол (выберите в меню)',
        reply_markup=kb.sex
    )
    await PersonChars.sex.set()


@dp.callback_query_handler(state=None, text='lookup_data')
async def get_data(callback: types.CallbackQuery):
    logger.info(f'Формируется промпт для {callback.from_user.id}')
    data = await dal.User.select_attributes(callback.from_user.id)
    await callback.message.answer(
        f'Формируется промпт'
    )
    timetable, recipes, shopping_list, trainings = await fill_prompt(data)
    await dal.Timetable.update_timetable(callback.from_user.id, timetable)
    await dal.Recipes.update_recipes(callback.from_user.id, 'monday', recipes)
    await dal.ShoppingList.update_shopping_list(callback.from_user.id, shopping_list)
    await dal.Trainings.update_trainings(callback.from_user.id, 'monday', trainings)

    await TimetableDays.monday.set()
    timetable = await dal.Timetable.get_timetable(callback.from_user.id)
    await callback.message.answer(
        f'Вот ваше расписание на понедельник:\n{timetable.monday}',
        reply_markup=kb.timetable
    )


@dp.callback_query_handler(state=None, text='SHOW_TIMETABLE')
async def show_timetable(callback: types.CallbackQuery):
    await TimetableDays.monday.set()
    timetable = await dal.Timetable.get_timetable(callback.from_user.id)
    await callback.message.answer(
        f'Вот ваше расписание на понедельник:\n{timetable.monday}',
        reply_markup=kb.timetable
    )


@dp.callback_query_handler(state=[TimetableDays.monday,
                                  TimetableDays.tuesday,
                                  TimetableDays.wednesday,
                                  TimetableDays.thursday,
                                  TimetableDays.friday,
                                  TimetableDays.saturday,
                                  TimetableDays.sunday],
                           text='show_recipes')
async def show_recipes(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        f'Получаем ваши рецепты...'
    )
    time.sleep(2)
    current_state = await state.get_state()
    day_of_week = current_state.split(':')[1]
    recipes = await dal.Recipes.get_recipes_by_day_of_week(callback.from_user.id, day_of_week)

    while recipes is None:
        await callback.message.answer(
            f'Получаем ваши рецепты...'
        )
        time.sleep(2)

    await callback.message.answer(
        f'Вот ваши рецепты на {day_of_week}:\n{recipes}',
        reply_markup=kb.recipes
    )


@dp.callback_query_handler(state=[TimetableDays.monday,
                                  TimetableDays.tuesday,
                                  TimetableDays.wednesday,
                                  TimetableDays.thursday,
                                  TimetableDays.friday,
                                  TimetableDays.saturday,
                                  TimetableDays.sunday],
                           text='show_shopping_list')
async def show_shopping_list(callback: types.CallbackQuery):
    await callback.message.answer(
        f'Получаем ваш список продуктов для покупки...'
    )
    time.sleep(1)
    shopping_list = await dal.ShoppingList.get_shopping_list(callback.from_user.id)

    if shopping_list is None:
        await callback.message.answer(
            f'<b>Ваш список продуктов для покупки пуст</b>',
            reply_markup=kb.timetable
        )

    await callback.message.answer(
        f'Вот ваш список продуктов для покупки:\n{shopping_list}',
        reply_markup=kb.recipes
    )


@dp.callback_query_handler(state=[TimetableDays.monday,
                                  TimetableDays.tuesday,
                                  TimetableDays.wednesday,
                                  TimetableDays.thursday,
                                  TimetableDays.friday,
                                  TimetableDays.saturday,
                                  TimetableDays.sunday],
                           text='show_trainings')
async def show_trainings(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        f'Получаем ваши тренировки...'
    )
    time.sleep(2)
    current_state = await state.get_state()
    day_of_week = current_state.split(':')[1]
    trainings = await dal.Trainings.get_trainings_by_day_of_week(callback.from_user.id, day_of_week)

    while trainings is None:
        await callback.message.answer(
            f'Получаем ваши тренировки...'
        )
        time.sleep(2)

    await callback.message.answer(
        f'Вот ваши тренировки на {day_of_week}:\n{trainings}',
        reply_markup=kb.recipes
    )


@dp.callback_query_handler(state=[TimetableDays.monday,
                                  TimetableDays.tuesday,
                                  TimetableDays.wednesday,
                                  TimetableDays.thursday,
                                  TimetableDays.friday,
                                  TimetableDays.saturday,
                                  TimetableDays.sunday],
                           text='back_to_timetable')
@dp.callback_query_handler(state=None, text='SHOW_TIMETABLE')
async def show_timetable(callback: types.CallbackQuery):
    await TimetableDays.monday.set()
    timetable = await dal.Timetable.get_timetable(callback.from_user.id)
    await callback.message.answer(
        f'Вот ваше расписание на понедельник:\n{timetable.monday}',
        reply_markup=kb.timetable
    )

@dp.callback_query_handler(state=PersonChars.sex)
async def add_sex(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'sex_man':
        async with state.proxy() as data:
            data['sex'] = 'Мужской'
    if callback.data == 'sex_woman':
        async with state.proxy() as data:
            data['sex'] = 'Женский'

    await callback.message.answer('Укажите ваш возраст, сколько полных лет (введите число)')
    await PersonChars.age.set()


@dp.message_handler(state=PersonChars.age)
async def add_age(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await message.answer('Необходимо ввести численное значение')
    else:
        async with state.proxy() as data:
            data['age'] = message.text

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
            data['height'] = message.text

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
            data['weight'] = message.text

    await message.answer(
        'Есть ли у вас какие-либо хронические заболевания или ограничения по здоровью (напишите в свободной форме)'
    )
    await PersonChars.illnesses.set()


@dp.message_handler(state=PersonChars.illnesses)
async def add_illnesses(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['illnesses'] = message.text

    await message.answer(
        'Принимаете ли вы какие-нибудь лекарства на постоянной основе, '
        'если да, то какие или если нет, напишите “нет” (напишите в свободной форме)'
    )
    await PersonChars.drugs.set()


@dp.message_handler(state=PersonChars.drugs)
async def add_drugs(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['drugs'] = message.text

    await message.answer(
        'Оцените ваш уровень физической подготовки',
        reply_markup=kb.level_of_fitness
    )
    await PersonChars.level_of_fitness.set()


@dp.callback_query_handler(state=PersonChars.level_of_fitness)
async def add_level_of_fitness(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'beginner':
        async with state.proxy() as data:
            data['level_of_fitness'] = 'Начинающий'
    if callback.data == 'average':
        async with state.proxy() as data:
            data['level_of_fitness'] = 'Средний'
    if callback.data == 'experienced':
        async with state.proxy() as data:
            data['level_of_fitness'] = 'Опытный'

    await callback.message.answer(
        'Какова ваша основная цель?',
        reply_markup=kb.goal
    )
    await PersonChars.goal.set()


@dp.callback_query_handler(state=PersonChars.goal, text=['lose_weight', 'bulk', 'keep_form', 'improve_health'])
async def add_goal(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'lose_weight':
        async with state.proxy() as data:
            data['goal'] = 'Похудение'
    if callback.data == 'bulk':
        async with state.proxy() as data:
            data['goal'] = 'Набор мышечной массы'
    if callback.data == 'keep_form':
        async with state.proxy() as data:
            data['goal'] = 'Поддержание формы'
    if callback.data == 'improve_health':
        async with state.proxy() as data:
            data['goal'] = 'Улучшение здоровья'

    await callback.message.answer(
        'Желаемый результат через 3 месяца, например, потерять 5 кг,'
        ' или набрать 3 кг мышечной массы (напишите в свободной форме)'
    )

    await PersonChars.result.set()


@dp.callback_query_handler(state=PersonChars.goal, text=['goal_free_type'])
async def add_goal(callback: types.CallbackQuery):
    await callback.message.answer(
        'Какова ваша основная цель? (напишите в свободной форме)'
    )


@dp.message_handler(state=PersonChars.goal)
async def add_goal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['goal'] = message.text

    await message.answer(
        'Желаемый результат через 3 месяца, например, потерять 5 кг,'
        ' или набрать 3 кг мышечной массы (напишите в свободной форме)'
    )

    await PersonChars.result.set()


@dp.message_handler(state=PersonChars.result)
async def add_result(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['result'] = message.text

    await message.answer(
        'Есть ли у вас аллергии на продукты или которых вы избегаете? Если да, то какие? (напишите в свободной форме)'
    )

    await PersonChars.allergy.set()


@dp.message_handler(state=PersonChars.allergy)
async def add_allergy(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['allergy'] = message.text

    await message.answer(
        'Следуете ли вы какой-либо диете в данный момент?'
        ' Например: вегетарианская, веганская, безглютеновая и т.д. (напишите в свободной форме)'
    )

    await PersonChars.diet.set()


@dp.message_handler(state=PersonChars.diet)
async def add_diet(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['diet'] = message.text

    await message.answer(
        'Какое у вас предпочтительное количество приемов пищи в день? (напишите в свободной форме)'
    )

    await PersonChars.number_of_meals.set()


@dp.message_handler(state=PersonChars.number_of_meals)
async def add_number_of_meals(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['number_of_meals'] = message.text

    await message.answer(
        'Сколько дней в неделю вы готовы уделять тренировкам?'
    )

    await PersonChars.trainings_per_week.set()


@dp.message_handler(state=PersonChars.trainings_per_week)
async def add_trainings_per_week(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['trainings_per_week'] = message.text

    await message.answer(
        'Сколько времени вы готовы в среднем тратить на одну тренировку?',
        reply_markup=kb.train_time_amount
    )

    await PersonChars.train_time_amount.set()


@dp.callback_query_handler(state=PersonChars.train_time_amount)
async def add_train_time_amount(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == '30min':
        async with state.proxy() as data:
            data['train_time_amount'] = '30 минут'
    elif callback.data == '1hour':
        async with state.proxy() as data:
            data['train_time_amount'] = '1 час'
    elif callback.data == '1-2hours':
        async with state.proxy() as data:
            data['train_time_amount'] = '1-2 часа'
    elif callback.data == 'moreThan2hours':
        async with state.proxy() as data:
            data['train_time_amount'] = 'Более 2 часов'
    else:
        async with state.proxy() as data:
            data['train_time_amount'] = 'Не знаю'

    await callback.message.answer(
        'Есть ли у вас доступ к спортзалу или фитнес-центру?',
        reply_markup=kb.gym_access
    )

    await PersonChars.gym_access.set()


@dp.callback_query_handler(state=PersonChars.gym_access)
async def add_gym_access(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        async with state.proxy() as data:
            data['gym_access'] = 'Да'
            data['gym_equipment'] = 'Есть доступ к спортзалу'

        await dal.User.add_attributes(state, callback.from_user.id)
        await state.finish()
        await callback.message.answer(
            'Ваши данные были внесены в базу, формируется промпт'
        )

        prompt_data = await dal.User.select_attributes(callback.from_user.id)
        response_dict = await fill_prompt(prompt_data)
        for key, value in response_dict:
            await callback.message.answer(f'{key}:\n{value}')

    if callback.data == 'no':
        async with state.proxy() as data:
            data['gym_access'] = 'Нет'

        await callback.message.answer(
            'Есть ли у вас в доступе спортивное оборудование (гантели, эспандеры, фитбол и т.д.)?'
            ' (Напишите в свободной форме что у вас есть)'
        )
        await PersonChars.gym_access_NO.set()


@dp.message_handler(state=PersonChars.gym_access_NO)
async def add_gym_equipment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gym_equipment'] = message.text
    await dal.User.add_attributes(state, message.from_user.id)

    await state.finish()
    await message.answer(
        'Ваши данные были внесены в базу, формируется промпт'
    )

    prompt_data = await dal.User.select_attributes(message.from_user.id)
    response = await fill_prompt(prompt_data)

    await message.answer(response)

#
# @dp.message_handler(state='*')
# async def answer(message: types.Message, state: FSMContext):
#     if state is not GPT.gpt:
#         await state.set_state(GPT.gpt)
#
#     data = await state.get_data()
#     print(data)
#     if data == {}:
#         await state.update_data(gpt=ChatGPT())
#         data = await state.get_data()
#
#     text = message.text
#     reply = data['gpt'].chat(text)
#     await state.update_data(gpt=data['gpt'])
#
#     await message.reply(reply)
