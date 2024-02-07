import schemas


async def fill_man_prompt(prompt_data: schemas.PromptData, client_changes=None):
    prompt_text = f"""
Generate a program for 9 weeks for person's goals. 
Pay close attention to the count of exercises, workout time should be according to intensity. 
Then generate training days for the first week, based on user information, basic workout rules and information 
that you have from uploaded articles. Use full-body workouts, if there are less than 3 sessions per week. 
Workouts should be built according to user's intensity and uploaded file "Intensity information".
Instead of writing "% от 1ПМ" or "% from 1 personal max" you must write the exact calculated weight as a number in every such exercise 
except when only user's own weight is needed.
Don't write【21†source】 or anything similar.
Don't include more than 6 exercises in one training.
If a person has high experience, the first weeks should be as hard as the others.
You must only use exercises that are in the uploaded file named "available_exercises" and most of them should be "Базовое" or "Начинающий".
Now, do not show any information except for your 9 week workout plan and the first training day.
Split your workout plan and the first training by "----------".
Дай ответ на русском, вначале напиши, что будет в следующих 9 неделях, 
без подробностей, понятно для обывателя в таком формате: 
Неделя 1-3: ...
Неделя 4-5: ...

----------


Затем дай мне первый тренировочный день для демонстрации в формате:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...

Напиши числом, через сколько дней следующая тренировка.

Gender - male, 
Age - {prompt_data.age} years old,
Height - {prompt_data.height} cm, 
Weight - {prompt_data.weight} kg, 
Previous gym experience - {prompt_data.gym_experience},  
Desired goals - {prompt_data.goals}, 
Desired intensity of trainings - {prompt_data.intensity}, 
Health restrictions - {prompt_data.health_restrictions},
Deadlift max - {prompt_data.deadlift_results} kg,
Squats max - {prompt_data.squats_results} kg,
Bench press max - {prompt_data.bench_results} kg 
Trainings per week - {prompt_data.times_per_week}\n
"""

    prompt_text += f'Additionally: {client_changes}\n' if client_changes else '\n'

    return prompt_text


async def fill_woman_prompt(prompt_data: schemas.PromptData, client_changes=None):
    prompt_text = f"""
Generate a program for 9 weeks for person's goals. 
Pay close attention to the count of exercises, workout time should be according to intensity. 
Then generate training days for the first week, based on user information, basic workout rules and information 
that you have from uploaded articles. Use full-body workouts, if there are less than 3 sessions per week. 
Workouts should be built according to user's intensity and uploaded file "Intensity information".
Instead of writing "% от 1ПМ" or "% from 1 personal max" you must write the exact calculated weight as a number in every such exercise 
except when only user's own weight is needed.
Don't write【21†source】 or anything similar.
Don't include more than 6 exercises in one training.
If a person has high experience, the first weeks should be as hard as the others.
You must only use exercises that are in the uploaded file named "available_exercises" and most of them should be "Базовое" or "Начинающий".
Now, do not show any information except for your 9 week workout plan and the first training day.
Split your workout plan and the first training by "----------".
Дай ответ на русском, вначале напиши, что будет в следующих 9 неделях, 
без подробностей, понятно для обывателя в таком формате: 
Неделя 1-3: ...
Неделя 4-5: ...

----------


Затем дай мне первый тренировочный день для демонстрации в формате:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...

Напиши числом, через сколько дней следующая тренировка.

Gender - female, 
Age - {prompt_data.age} years old,
Height - {prompt_data.height} cm, 
Weight - {prompt_data.weight} kg, 
Previous gym experience - {prompt_data.gym_experience},  
Desired goals - {prompt_data.goals}, 
Desired intensity of trainings - {prompt_data.intensity}, 
Health restrictions - {prompt_data.health_restrictions}, 
Trainings per week - {prompt_data.times_per_week}\n
"""

    prompt_text += f'Additionally: {client_changes}\n' if client_changes else '\n'

    return prompt_text


async def fill_man_prompt_demo(
        workout_plan, client_edits_next_week=None
):
    prompt_text = f"""
I completed my 1st workout that you gave to me. My results: {workout_plan}, my comment: {client_edits_next_week}

Give me demonstration of one training of 7-9 weeks. It should constist of different exersises, sets and drop sets.
Don't write anything else except for the training. You must follow all instructions provided in my previous messages.
Don't include more than 6 exercises in one training.

Формат вывода тренировки:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...
"""
    return prompt_text


async def fill_woman_prompt_demo(
        workout_plan, client_edits_next_week=None
):
    prompt_text = f"""
I completed my 1st workout that you gave to me. My results: {workout_plan}, my comment: {client_edits_next_week}

Give me demonstration of one training of 7-9 weeks. It should constist of different exersises, sets and drop sets.
Don't write anything else except for the training. You must follow all instructions provided in my previous messages.
Don't include more than 6 exercises in one training.

Формат вывода тренировки:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...
"""
    return prompt_text


async def fill_prompt_end_of_trial():
    prompt_text = f"""
Напоминаю, что я выполнил первую тренировку и поделился результатами, 
теперь тебе необходимо отправить мне оставшиеся тренировочные дни недели 1.
Don't write anything else except for the trainings. You must follow all instructions provided in my previous messages.
Don't include more than 6 exercises in one training.

Формат вывода тренировки:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...
"""

    return prompt_text


async def fill_man_prompt_next_week(
        workout_plan, week, client_edits_next_week=None
):
    prompt_text = f"""
I completed my {week - 1} workout week. My results: {workout_plan}, my comment: {client_edits_next_week}

Give me trainings for next week, use my information, I have sent before.

Don't write anything else except for the trainings. You must follow all instructions provided in my previous messages.
Don't include more than 6 exercises in one training.

Формат вывода тренировки:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...
"""
    return prompt_text


async def fill_woman_prompt_next_week(
        workout_plan, week, client_edits_next_week=None
):
    prompt_text = f"""
I completed my {week - 1} workout week. My results: {workout_plan}, my comment: {client_edits_next_week}

Give me trainings for next week, use my information, I have sent before.

Don't write anything else except for the trainings. You must follow all instructions provided in my previous messages.
Don't include more than 6 exercises in one training.

Формат вывода тренировки:
День 1:  (тип тренировки) | Неделя 1

-  упражнение - 140 кг (собственный вес) - 4 подхода - 5 повторений - отдых между повторениями 2.5 минуты
...
"""
    return prompt_text


async def fill_meal_plan_prompt_text_trial(
        prompt_data: schemas.PromptData,
):
    prompt_text = f"""
You made a 9 week training plan for a person, use this person's information to make nutrition plan for 1 week.
Make it not expensive, don't include protein powder and use common ingredients and recipies.
 
Gender - male, 
Age - {prompt_data.age} years old,
Height - {prompt_data.height} cm, 
Weight - {prompt_data.weight} kg, 
Previous gym experience - {prompt_data.gym_experience},  
Desired goals - {prompt_data.goals}, 
Desired intensity of trainings - {prompt_data.intensity}, 
Health restrictions - {prompt_data.health_restrictions}, 
allergies and food intolerances - {prompt_data.allergy},
Trainings per week - {prompt_data.times_per_week}\n

Only a one-week food plan is required. 
Дай ответ на русском,  дай мне план питания на один день первой недели для демонстрации. 
Не пиши ничего кроме плана питания. Пиши номер плана, пример: “Питание 1”, учитывая, что в неделе 7 дней.
"""
    return prompt_text


async def fill_meal_plan_prompt_text_end_of_trial():
    prompt_text = f"""
You made me a nutrition plan for the 1st day of the 1st week. Make me nutrition plan for the other 6 days.
Split the days with "----------"
Дай ответ на русском. 
Не пиши ничего кроме плана питания. Пиши номер плана, пример: “Питание 1”, учитывая, что в неделе 7 дней.
"""
    return prompt_text


async def fill_meal_plan_prompt_text_next_week(
        prompt_data: schemas.PromptData,
        week=2
):
    prompt_text = f"""
Based on my information create a nutrition plan for {week} week. Only a one-week food plan is required. 
Split the days with "----------"

Gender - male, 
Age - {prompt_data.age} years old,
Height - {prompt_data.height} cm, 
Weight - {prompt_data.weight} kg, 
Previous gym experience - {prompt_data.gym_experience},  
Desired goals - {prompt_data.goals}, 
Desired intensity of trainings - {prompt_data.intensity}, 
Health restrictions - {prompt_data.health_restrictions}, 
allergies and food intolerances - {prompt_data.allergy},
Trainings per week - {prompt_data.times_per_week}\n

Only a one-week food plan is required. 
Дай ответ на русском,  дай мне план питания на один день первой недели для демонстрации. 
Не пиши ничего кроме плана питания. Пиши номер плана, пример: “Питание 1”, учитывая, что в неделе 7 дней.
"""
    return prompt_text
