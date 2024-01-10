import schemas


async def fill_man_prompt(prompt_data: schemas.PromptData, client_changes=None):
    prompt_text = f"""
Make a 9 weeks training plan, pay attention to health restricitions, delete exersises if it has them. 
Gender - male, 
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

    prompt_text += """
A 9 week progressive training program and food plan is required. 
Дай ответ на русском, вначале напиши, что будет в следующих 9 неделях типа: 
Неделя 1-3: Баз.. пиши понятно для обывателя, а потом дай мне одну первую тренировку первой недели, 
то есть первый тренировочный день для демонстрации. Не давай фулбади тренировки, 
если Trainings per week - 4. Напиши, через сколько дней следующая тренировка."""

    return prompt_text


async def fill_woman_prompt(prompt_data: schemas.PromptData, client_changes=None):
    prompt_text = f"""
    Make a 9 weeks training plan, pay attention to health restricitions, delete exersises if it has them. 
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

    prompt_text += """
    A 9 week progressive training program and food plan is required. 
    Дай ответ на русском, вначале напиши, что будет в следующих 9 неделях типа: 
    Неделя 1-3: Баз.. пиши понятно для обывателя, а потом дай мне одну первую тренировку первой недели, 
    то есть первый тренировочный день для демонстрации. Не давай фулбади тренировки, 
    если Trainings per week - 4. Напиши, через сколько дней следующая тренировка."""

    return prompt_text


async def fill_man_prompt_next_week(
        workout_plan, client_edits_next_week=None
):
    prompt_text = f"""
I completed this 1st workout. My results: {workout_plan}, my comment: {client_edits_next_week}

Give me demonstration of one training of 7-9 weeks. It should be different exersises and sets and drop sets.
"""
    return prompt_text


async def fill_woman_prompt_next_week(
        workout_plan, client_edits_next_week=None
):
    prompt_text = f"""
I completed this 1st workout. My results: {workout_plan}, my comment: {client_edits_next_week}

Give me demonstration of one training of 7-9 weeks. It should be different exersises and sets and drop sets.
"""
    return prompt_text


async def fill_man_meal_plan_prompt(
        prompt_data: schemas.PromptData,
):
    prompt_text = f"""
You made 9 week training plan, use next information to make nutrition plan for 1 week. 
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

A 1 week food plan is required. 
Дай ответ на русском,  дай мне план питания на один день первой недели для демонстрации. 
Не пиши ничего кроме плана питания. Пиши номер плана, пример: “Питание 1”, учитывая, что в неделе 7 дней.
"""
    return prompt_text


async def fill_woman_meal_plan_prompt(
        prompt_data: schemas.PromptData,
):
    prompt_text = f"""
You made 9 week training plan, use next information to make nutrition plan for 1 week. 
Gender - female, 
Age - {prompt_data.age} years old,
Height - {prompt_data.height} cm, 
Weight - {prompt_data.weight} kg, 
Previous gym experience - {prompt_data.gym_experience},  
Desired goals - {prompt_data.goals}, 
Desired intensity of trainings - {prompt_data.intensity}, 
Health restrictions - {prompt_data.health_restrictions}, 
allergies and food intolerances - {prompt_data.allergy},
Trainings per week - {prompt_data.times_per_week}\n

A 1 week food plan is required. 
Дай ответ на русском,  дай мне план питания на один день первой недели для демонстрации. 
Не пиши ничего кроме плана питания. Пиши номер плана, пример: “Питание 1”, учитывая, что в неделе 7 дней.
"""
    return prompt_text
