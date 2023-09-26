from aiogram.dispatcher.filters.state import State, StatesGroup


class PersonChars(StatesGroup):
    sex = State()
    age = State()
    height = State()
    weight = State()
    illnesses = State()
    drugs = State()
    level_of_fitness = State()
    goal = State()
    result = State()
    allergy = State()
    diet = State()
    number_of_meals = State()
    trainings_per_week = State()
    train_time_amount = State()
    gym_access = State()
    gym_access_YES = State()
    gym_access_NO = State()


class GPT(StatesGroup):
    gpt = State()


class TimetableDays(StatesGroup):
    monday = State()
    tuesday = State()
    wednesday = State()
    thursday = State()
    friday = State()
    saturday = State()
    sunday = State()


timetable_states_list = [
    TimetableDays.monday,
    TimetableDays.tuesday,
    TimetableDays.wednesday,
    TimetableDays.thursday,
    TimetableDays.friday,
    TimetableDays.saturday,
    TimetableDays.sunday
]

timetable_states_str_list = [
    'TimetableDays:monday',
    'TimetableDays:tuesday',
    'TimetableDays:wednesday',
    'TimetableDays:thursday',
    'TimetableDays:friday',
    'TimetableDays:saturday',
    'TimetableDays:sunday'
]

days_translation = {
    'monday': 'понедельник',
    'tuesday': 'вторник',
    'wednesday': 'среду',
    'thursday': 'четверг',
    'friday': 'пятницу',
    'saturday': 'субботу',
    'sunday': 'воскресенье'
}