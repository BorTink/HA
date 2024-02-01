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
    allergy = State()
    times_per_week = State()


class GPT(StatesGroup):
    gpt = State()


class BaseStates(StatesGroup):
    show_trainings = State()
    rebuild_workouts = State()
    start_workout = State()
    add_weight = State()
    meals = State()
    support = State()
    add_review = State()
    end_of_week_changes = State()
    end_of_trial = State()
    subscription_proposition = State()


class SubStates(StatesGroup):
    show_add_training = State()
    trainings_and_food = State()
    trainings_and_food_9_weeks = State()


class Admin(StatesGroup):
    assistant_training = State()
