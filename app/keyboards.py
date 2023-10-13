from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

always_markup = ReplyKeyboardMarkup(resize_keyboard=True)
always_markup_1 = KeyboardButton('Купить подписку')
always_markup.add(always_markup_1)

main = InlineKeyboardMarkup(resize_keyboard=True)
main_1 = InlineKeyboardButton('Повторно составить расписание', callback_data='lookup_data')
main_2 = InlineKeyboardButton('Показать свое расписание', callback_data='SHOW_TIMETABLE')
main_3 = InlineKeyboardButton('Обновить свои данные', callback_data='update_data')
main.add(main_1).add(main_2).add(main_3)

timetable = InlineKeyboardMarkup(resize_keyboard=True)
timetable_1 = InlineKeyboardButton('Показать рецепты', callback_data='show_recipes')
timetable_2 = InlineKeyboardButton('Показать тренировки', callback_data='show_trainings')
timetable_4 = InlineKeyboardButton('Следующий день', callback_data='show_next_day')
timetable_5 = InlineKeyboardButton('Предыдущий день', callback_data='show_prev_day')
timetable_6 = InlineKeyboardButton('Вернуться в меню', callback_data='back_to_menu')
timetable.add(timetable_1).add(timetable_2).add(timetable_4, timetable_5).add(timetable_6)

recipes = InlineKeyboardMarkup(resize_keyboard=True)
recipes_1 = InlineKeyboardButton('Вернуться к расписанию', callback_data='back_to_timetable')
recipes.add(recipes_1)

main_new = InlineKeyboardMarkup(resize_keyboard=True)
main_new_1 = InlineKeyboardButton('Ввести свои данные', callback_data='insert_data')
main_new.add(main_new_1)

gender = InlineKeyboardMarkup(resize_keyboard=True)
gender_1 = InlineKeyboardButton('Мужской', callback_data='gender_man')
gender_2 = InlineKeyboardButton('Женский', callback_data='gender_woman')
gender.add(gender_1, gender_2)

intensity = InlineKeyboardMarkup(resize_keyboard=True)
intensity_1 = InlineKeyboardButton('🧑‍💼 Низкую', callback_data='low')
intensity_2 = InlineKeyboardButton('👨‍🎓 Среднюю', callback_data='moderate')
intensity_3 = InlineKeyboardButton('🥷 Высокую', callback_data='high')
intensity.add(intensity_1).add(intensity_2).add(intensity_3)

goal = InlineKeyboardMarkup(resize_keyboard=True)
goal_1 = InlineKeyboardButton('⚖️ Похудение', callback_data='lose_weight')
goal_2 = InlineKeyboardButton('💪 Набор мышечной массы', callback_data='bulk')
goal_3 = InlineKeyboardButton('🏊 Поддержание формы', callback_data='keep_form')
goal_4 = InlineKeyboardButton('🍃 Улучшение здоровья', callback_data='improve_health')
goal_5 = InlineKeyboardButton('↪️ Другое (свободный ввод)', callback_data='goal_free_type')
goal.add(goal_1, goal_2).add(goal_3).add(goal_4).add(goal_5)

train_time_amount = InlineKeyboardMarkup(resize_keyboard=True)
train_time_amount_1 = InlineKeyboardButton('30 минут', callback_data='30min')
train_time_amount_2 = InlineKeyboardButton('1 час', callback_data='1hour')
train_time_amount_3 = InlineKeyboardButton('1-2 часа', callback_data='1-2hours')
train_time_amount_4 = InlineKeyboardButton('Более 2 часов', callback_data='moreThan2hours')
train_time_amount.add(train_time_amount_1, train_time_amount_2).add(train_time_amount_3, train_time_amount_4)

gym_access = InlineKeyboardMarkup(resize_keyboard=True)
gym_access_1 = InlineKeyboardButton('Да', callback_data='yes')
gym_access_2 = InlineKeyboardButton('Нет', callback_data='no')
gym_access.add(gym_access_1, gym_access_2)
