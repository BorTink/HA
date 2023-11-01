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
    focus = State()
    intensity = State()
    health_restrictions = State()
    times_per_week = State()


class GPT(StatesGroup):
    gpt = State()


class BaseStates(StatesGroup):
    show_trainings = State()
    rebuild_workouts = State()
