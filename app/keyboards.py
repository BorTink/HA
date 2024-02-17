from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

always_markup = ReplyKeyboardMarkup(resize_keyboard=True)
always_markup_1 = KeyboardButton('Вернуться в главное меню')
always_markup_2 = KeyboardButton('Техподдержка / Оставить отзыв')
always_markup.add(always_markup_1).add(always_markup_2)

user_info = ReplyKeyboardMarkup(resize_keyboard=True)
user_info_1 = KeyboardButton('Вернуться в начало анкеты')
user_info.add(user_info_1)

support = InlineKeyboardMarkup(resize_keyboard=True)
support_1 = InlineKeyboardButton('Техподдержка', callback_data='tech_support')
support_2 = InlineKeyboardButton('Оставить отзыв', callback_data='add_review')
support.add(support_1).add(support_2)

first_training_proposition = InlineKeyboardMarkup()
first_training_proposition_1 = InlineKeyboardButton('🔎 Посмотреть', callback_data='watch_proposition')
first_training_proposition_2 = InlineKeyboardButton('⏭ Пропустить и перейти далее', callback_data='skip_proposition')
first_training_proposition.add(first_training_proposition_1).add(first_training_proposition_2)

continue_keyboard = InlineKeyboardMarkup()
continue_keyboard_1 = InlineKeyboardButton('➡️ Перейти далее', callback_data='continue')
continue_keyboard.add(continue_keyboard_1)

subscribe = InlineKeyboardMarkup()
subscribe_1 = InlineKeyboardButton('199 руб./ мес.', callback_data='trainings_and_food')
subscribe_2 = InlineKeyboardButton('399 руб./ 9 недель', callback_data='trainings_and_food_9_weeks')
subscribe.add(subscribe_1).add(subscribe_2)

subscribe_proposition = InlineKeyboardMarkup()
subscribe_proposition_1 = InlineKeyboardButton('✅ Оформить подписку', callback_data='get_subscription')
subscribe_proposition_2 = InlineKeyboardButton('⏸ Вернуться позднее', callback_data='subscribe_later')
subscribe_proposition.add(subscribe_proposition_1).add(subscribe_proposition_2)

main = InlineKeyboardMarkup(resize_keyboard=True)
main_1 = InlineKeyboardButton('Показать расписание', callback_data='SHOW_TIMETABLE')
main.add(main_1)

main_admin = InlineKeyboardMarkup(resize_keyboard=True)
main_admin_1 = InlineKeyboardButton('Перейти к тестированию ассистента', callback_data='ADMIN_go_to_assistant_testing')
main_admin.add(main_admin_1).add(main_1)

main_new = InlineKeyboardMarkup(resize_keyboard=True)
main_new_1 = InlineKeyboardButton('🔓 Начать пробный период', callback_data='insert_data')
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
expected_results.add(expected_results_1).add(expected_results_2)

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

show_program = InlineKeyboardMarkup(resize_keyboard=True)
show_program_1 = InlineKeyboardButton('Продолжить', callback_data='continue')
show_program.add(show_program_1)

trainings_tab = InlineKeyboardMarkup(resize_keyboard=True)
trainings_tab_1 = InlineKeyboardButton('Пересобрать все тренировки', callback_data='rebuild_workouts')
trainings_tab_2 = InlineKeyboardButton('Начать активную тренировку', callback_data='start_workout')
trainings_tab_3 = InlineKeyboardButton('Предыдущая тренировка', callback_data='prev_workout')
trainings_tab_4 = InlineKeyboardButton('Следующая тренировка', callback_data='next_workout')
trainings_tab_5 = InlineKeyboardButton('🥑 План питания', callback_data='meal_plan')
trainings_tab_6 = InlineKeyboardButton('Пересобрать тренировку', callback_data='rebuild_workouts')
trainings_tab.add(trainings_tab_6)
trainings_tab.add(trainings_tab_5)
trainings_tab.add(trainings_tab_1).add(trainings_tab_2).add(trainings_tab_3, trainings_tab_4)

trainings_tab_without_prev = InlineKeyboardMarkup(resize_keyboard=True)
trainings_tab_without_prev_3 = InlineKeyboardButton('-', callback_data='-')
trainings_tab_without_prev.add(trainings_tab_1).add(trainings_tab_2).add(trainings_tab_without_prev_3, trainings_tab_4)
trainings_tab_without_prev.add(trainings_tab_5)

trainings_tab_without_next = InlineKeyboardMarkup(resize_keyboard=True)
trainings_tab_without_next_4 = InlineKeyboardButton('-', callback_data='-')
trainings_tab_without_next.add(trainings_tab_1).add(trainings_tab_2).add(trainings_tab_3, trainings_tab_without_next_4)
trainings_tab_without_next.add(trainings_tab_5)

start_workout = InlineKeyboardMarkup(resize_keyboard=True)
start_workout_1 = InlineKeyboardButton('Начать тренировку', callback_data='insert_weights')
start_workout_2 = InlineKeyboardButton('Вернуться назад', callback_data='go_back')
start_workout.add(start_workout_1).add(start_workout_2)

insert_weights_in_workout = InlineKeyboardMarkup(resize_keyboard=True)
insert_weights_in_workout_1 = InlineKeyboardButton('Ввести вес', callback_data='add_weight')
insert_weights_in_workout_2 = InlineKeyboardButton('Завершить тренировку', callback_data='complete_workout')
insert_weights_in_workout_3 = InlineKeyboardButton('🥑 План питания', callback_data='meal_plan')
insert_weights_in_workout_4 = InlineKeyboardButton('Пересобрать тренировку', callback_data='rebuild_workouts')
insert_weights_in_workout.add(insert_weights_in_workout_4)
insert_weights_in_workout.add(insert_weights_in_workout_3)
insert_weights_in_workout.add(insert_weights_in_workout_1, insert_weights_in_workout_2)



insert_weight = InlineKeyboardMarkup(resize_keyboard=True)
insert_weight_1 = InlineKeyboardButton('Перейти к следующему упражнению', callback_data='next_exercise')
insert_weight_2 = InlineKeyboardButton('Перейти к предыдущему упражнению', callback_data='prev_exercise')
insert_weight.add(insert_weight_1).add(insert_weight_2)

meal_plan_trial = InlineKeyboardMarkup()
meal_plan_trial_3 = InlineKeyboardButton('Тренировка', callback_data='go_to_workout')
meal_plan_trial.add(meal_plan_trial_3)

meal_plan = InlineKeyboardMarkup()
meal_plan_1 = InlineKeyboardButton('Предыдущий день', callback_data='prev_meal_day')
meal_plan_2 = InlineKeyboardButton('Следующий день', callback_data='next_meal_day')
meal_plan.add(meal_plan_1, meal_plan_2).add(meal_plan_trial_3)

meal_plan_without_prev = InlineKeyboardMarkup()
meal_plan_without_prev_1 = InlineKeyboardButton('-', callback_data='-')
meal_plan_without_prev.add(meal_plan_without_prev_1, meal_plan_2).add(meal_plan_trial_3)

meal_plan_without_next = InlineKeyboardMarkup()
meal_plan_without_next_2 = InlineKeyboardButton('-', callback_data='-')
meal_plan_without_next.add(meal_plan_1, meal_plan_without_next_2).add(meal_plan_trial_3)

complete_workout = InlineKeyboardMarkup(resize_keyboard=True)
complete_workout_1 = InlineKeyboardButton('Да', callback_data='yes')
complete_workout_2 = InlineKeyboardButton('Нет', callback_data='no')
complete_workout.add(complete_workout_1, complete_workout_2)
