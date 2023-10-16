from aiogram.dispatcher.filters.state import State, StatesGroup


class PersonChars(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    gym_experience = State()
    max_results = State()

    bench_results = State()
    deadlift_results = State()
    squats_results = State()

    goals = State()
    intensity = State()
    health_restrictions = State()
    times_per_week = State()


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