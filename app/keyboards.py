from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

always_markup = ReplyKeyboardMarkup(resize_keyboard=True)
always_markup_1 = KeyboardButton('Купить подписку')
always_markup.add(always_markup_1)

recipes = InlineKeyboardMarkup(resize_keyboard=True)
recipes_1 = InlineKeyboardButton('Вернуться к расписанию', callback_data='back_to_timetable')
recipes.add(recipes_1)

main = InlineKeyboardMarkup(resize_keyboard=True)
main_1 = InlineKeyboardButton('Сгенерировать тренировки', callback_data='generate_trainings')
main.add(main_1)

main_new = InlineKeyboardMarkup(resize_keyboard=True)
main_new_1 = InlineKeyboardButton('Приступить к созданию тренировок', callback_data='insert_data')
main_new.add(main_new_1)

gender = InlineKeyboardMarkup(resize_keyboard=True)
gender_1 = InlineKeyboardButton('Мужской', callback_data='gender_man')
gender_2 = InlineKeyboardButton('Женский', callback_data='gender_woman')
gender.add(gender_1, gender_2)

gym_experience = InlineKeyboardMarkup(resize_keyboard=True)
gym_experience_1 = InlineKeyboardButton('Начинающий', callback_data='beginner')
gym_experience_2 = InlineKeyboardButton('Средний', callback_data='medium')
gym_experience_3 = InlineKeyboardButton('Опытный (могу сам тренировать)', callback_data='experienced')
gym_experience.add(gym_experience_1).add(gym_experience_2).add(gym_experience_3)

max_results = InlineKeyboardMarkup(resize_keyboard=True)
max_results_1 = InlineKeyboardButton('Да', callback_data='yes')
max_results_2 = InlineKeyboardButton('Нет', callback_data='no')
max_results.add(max_results_1, max_results_2)

intensity = InlineKeyboardMarkup(resize_keyboard=True)
intensity_1 = InlineKeyboardButton('🧑‍💼 Умеренная', callback_data='low')
intensity_2 = InlineKeyboardButton('👨‍🎓 Средняя', callback_data='moderate')
intensity_3 = InlineKeyboardButton('🥷 Высокая', callback_data='high')
intensity.add(intensity_1).add(intensity_2).add(intensity_3)

times_per_week = InlineKeyboardMarkup(resize_keyboard=True)
times_per_week_1 = InlineKeyboardButton('2', callback_data='2')
times_per_week_2 = InlineKeyboardButton('3', callback_data='3')
times_per_week_3 = InlineKeyboardButton('4', callback_data='4')
times_per_week.add(times_per_week_1, times_per_week_2, times_per_week_3)

trainings_tab = InlineKeyboardMarkup(resize_keyboard=True)
trainings_tab_1 = InlineKeyboardButton('Пересобрать тренировку', callback_data='rebuild_workout')
trainings_tab_2 = InlineKeyboardButton('Начать тренировку', callback_data='start_workout')
trainings_tab.add(trainings_tab_1).add(trainings_tab_2)
