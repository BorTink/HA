from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

always_markup = ReplyKeyboardMarkup(resize_keyboard=True)
always_markup_1 = KeyboardButton('Купить подписку')
always_markup_2 = KeyboardButton('Вернуться в главное меню')
always_markup.add(always_markup_1).add(always_markup_2)

recipes = InlineKeyboardMarkup(resize_keyboard=True)
recipes_1 = InlineKeyboardButton('Вернуться к расписанию', callback_data='back_to_timetable')
recipes.add(recipes_1)

main = InlineKeyboardMarkup(resize_keyboard=True)
main_2 = InlineKeyboardButton('Показать расписание', callback_data='SHOW_TIMETABLE')
main.add(main_2)

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

expected_results = InlineKeyboardMarkup(resize_keyboard=True)
expected_results_1 = InlineKeyboardButton('Набор массы', callback_data='muscle gain')
expected_results_2 = InlineKeyboardButton('Улучшение рельефа (снижение веса)', callback_data='weight loss')
expected_results.add(expected_results_1, expected_results_2)

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
trainings_tab_1 = InlineKeyboardButton('Пересобрать все тренировки', callback_data='rebuild_workouts')
trainings_tab_2 = InlineKeyboardButton('Начать активную тренировку', callback_data='start_workout')
trainings_tab_3 = InlineKeyboardButton('Предыдущая тренировка', callback_data='prev_workout')
trainings_tab_4 = InlineKeyboardButton('Следующая тренировка', callback_data='next_workout')
trainings_tab.add(trainings_tab_1).add(trainings_tab_2).add(trainings_tab_3, trainings_tab_4)

trainings_tab_without_prev = InlineKeyboardMarkup(resize_keyboard=True)
trainings_tab_without_prev_1 = InlineKeyboardButton('Пересобрать все тренировки', callback_data='rebuild_workouts')
trainings_tab_without_prev_2 = InlineKeyboardButton('Начать активную тренировку', callback_data='start_workout')
trainings_tab_without_prev_3 = InlineKeyboardButton('Следующая тренировка', callback_data='next_workout')
trainings_tab_without_prev.add(
    trainings_tab_without_prev_1
).add(trainings_tab_without_prev_2).add(trainings_tab_without_prev_3)

trainings_tab_without_next = InlineKeyboardMarkup(resize_keyboard=True)
trainings_tab_without_next_1 = InlineKeyboardButton('Пересобрать все тренировки', callback_data='rebuild_workouts')
trainings_tab_without_next_2 = InlineKeyboardButton('Начать активную тренировку', callback_data='start_workout')
trainings_tab_without_next_3 = InlineKeyboardButton('Предыдущая тренировка', callback_data='prev_workout')
trainings_tab_without_next.add(
    trainings_tab_without_next_1
).add(trainings_tab_without_next_2).add(trainings_tab_without_next_3)

start_workout = InlineKeyboardMarkup(resize_keyboard=True)
start_workout_1 = InlineKeyboardButton('Начать тренировку', callback_data='insert_weights')
start_workout_2 = InlineKeyboardButton('Вернуться назад', callback_data='go_back')
start_workout.add(start_workout_1).add(start_workout_2)

insert_weights_in_workout = InlineKeyboardMarkup(resize_keyboard=True)
insert_weights_in_workout_1 = InlineKeyboardButton('Пропустить', callback_data='skip_weight')
insert_weights_in_workout_2 = InlineKeyboardButton('Ввести вес', callback_data='add_weight')
insert_weights_in_workout_3 = InlineKeyboardButton('Покинуть тренировку', callback_data='leave_workout')
insert_weights_in_workout.add(insert_weights_in_workout_1, insert_weights_in_workout_2).add(insert_weights_in_workout_3)

insert_weight = InlineKeyboardMarkup(resize_keyboard=True)
insert_weight_1 = InlineKeyboardButton('Вернуться к тренировке', callback_data='return_to_training')
insert_weight.add(insert_weight_1)

leave_workout = InlineKeyboardMarkup(resize_keyboard=True)
leave_workout_1 = InlineKeyboardButton('Да', callback_data='yes')
leave_workout_2 = InlineKeyboardButton('Нет', callback_data='no')
leave_workout.add(leave_workout_1, leave_workout_2)

