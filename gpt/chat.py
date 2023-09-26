import re

import openai
from loguru import logger

import dal
import schemas

openai.api_key = "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"


class ChatGPT:
    def __init__(self):
        openai.api_key = "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"
        self.starting_message = {"role": "system", "content": "You are a gym training tutor bot designed to create meal"
                                                              " and training plans"}
        self.messages = [
            self.starting_message
        ]

    def chat(self, message):
        self.messages.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.messages,
            max_tokens=3100
        )
        return response["choices"][0]["message"].content

    def gpt_create_timetable(self, message):
        self.messages.append({"role": "user", "content": message})
        logger.info(f'Длина промпта для расписания '
                    f'- {len(self.messages[0]["content"].split()) + len(self.messages[1]["content"].split())} слов')
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.messages,
            max_tokens=3500
        )
        self.messages = [
            self.starting_message,
            {"role": "assistant", "content": response["choices"][0]["message"].content}
        ]
        logger.info(f'Длина расписания '
                    f'- {len(self.messages[1]["content"].split())} слов')
        logger.info(f'Все расписание - {response["choices"][0]["message"]["content"]}')

        return response["choices"][0]["message"]['content']

    def gpt_get_recipes(self, timetable, recipes_message):
        recipes = {}
        for day, timetable_message in timetable.items():
            self.messages = [
                self.starting_message,
                {'role': "assistant", 'content': timetable_message},
                {"role": "user", "content": recipes_message}
            ]

            logger.info(self.messages[1])
            logger.info(f'Длина промпта для рецептов на {day}'
                        f'- {len(self.messages[0]["content"].split()) + len(self.messages[1]["content"].split()) + len(self.messages[2]["content"].split())} слов')
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=self.messages,
                max_tokens=1500
            )
            recipes[f'{day}'] = (response["choices"][0]["message"]['content'])

            logger.info(f'Длина рецептов на {day} '
                        f'- {len(self.messages[0]["content"].split()) + len(self.messages[1]["content"].split())} слов')
        return recipes

    def gpt_get_trainings(self, timetable, prompt_trainings):
        trainings = {}
        for day, timetable_message in timetable.items():
            self.messages = [
                self.starting_message,
                {'role': "assistant", 'content': timetable_message},
                {"role": "user", "content": prompt_trainings}
            ]
            self.messages.append({"role": "user", "content": prompt_trainings})
            logger.info(f'Длина промпта для тренировок на {day} '
                        f'- {len(self.messages[0]["content"].split()) + len(self.messages[1]["content"].split()) + len(self.messages[2]["content"].split())} слов')
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=self.messages,
                max_tokens=1500
            )
            logger.info(f'Длина тренировок на {day}'
                        f'- {len(response["choices"][0]["message"]["content"].split())} слов')

            trainings[f'{day}'] = (response["choices"][0]["message"]['content'])
        return trainings


async def fill_prompt(prompt_data: schemas.PromptData):
    prompt_text = f"""
    Представь, что ты профессиональный тренер и нутрицолог. У тебя есть клиент, которому ты должен составить план питания и тренировок на каждый день недели (необходимо, чтобы на каждый день был разный план питания). Снизу есть данные клиента, на основе которых ты должен составить макимально унифицированный индивидуальный план тренировок и питания. Для тренировок обязательно подстраивай количество подходов и повторений под цель клиента, то есть, если набор мышечной массы, то нужно минимальное количество повторений (6-8) и тд. Разбей тренировки по группам мышц и начинай первую тренировку недели с верхней части тела. Также добавь примерное количество кг для каждого упражнения, учитывая средние способности при данных его анкеты и. План питания планируй в расчете на цели клиента. Выдай все в таком формате:

    "Понедельник:
    
    ("день тренировки") (если она есть, если тренировки в этот день нет, то "день отдыха")
    
    Тренировка:
    Приседания со штангой: ...
    Приемы пищи:
    
    Завтрак:
    ...
    Обед: ... и тд. (смотри, сколько приемов пищи пишет клиент)”

    Нужно вывести расписание для каждого дня недели, нельзя объединять расписание для разных дней в одно, особенно субботу и воскресенье

    Анкета клиента:

    Пол - {prompt_data.sex}
    Возраст (полных лет) - {prompt_data.age}
    Рост (см) - {prompt_data.height}
    Вес (кг) - {prompt_data.weight}
    Есть ли хронические заболевания - {prompt_data.illnesses} 
    Уровень физической подготовки - {prompt_data.level_of_fitness}
    Основная цель - {prompt_data.goal}
    Желаемый результат через 3 месяца - {prompt_data.result} 
    Аллергии или избегаемые продукты - {prompt_data.allergy}
    Диеты - {prompt_data.diet}
    Предпочтительное количество приемов пищи - {prompt_data.number_of_meals}
    Количество дней в неделю готов уделять тренировкам - {prompt_data.trainings_per_week}
    Сколько готов уделять одной тренировке в среднем - {prompt_data.train_time_amount}
    Доступ в спортзалу - {prompt_data.gym_access}
    Если, нет доступа в зал, то какое есть оборудование - {prompt_data.gym_equipment}
    """

    chat = ChatGPT()

    timetable = chat.gpt_create_timetable(prompt_text).replace(':\n\n', '')

    timetable_list = re.split(
        'Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье', timetable)
    timetable_dict = {
        'monday': timetable_list[1],
        'tuesday': timetable_list[2],
        'wednesday': timetable_list[3],
        'thursday': timetable_list[4],
        'friday': timetable_list[5],
        'saturday': timetable_list[6],
        'sunday': timetable_list[7],
    }

    meals_dict = {}
    trainings_dict = {}

    for day, timetable_message in timetable_dict.items():
        item_temp = timetable_message.split('Приемы пищи')
        meals = item_temp[1]
        meals_dict[day] = meals

        if 'Тренировка' in timetable_message:
            item_temp = item_temp[0].split('Тренировка')
            trainings = item_temp[1]
            trainings_dict[day] = trainings

    prompt_recipes = f"""
Напиши мне подробные рецепты для приемов пищи, которые ты составил. Не давай дополнительных комментариев
"""
    prompt_trainings = f"""
Напиши мне подробную текстовую инструкцию к тренировке, которую ты составил, если она есть. Не давай дополнительных комментариев
"""

    recipes = chat.gpt_get_recipes(meals_dict, prompt_recipes)

    trainings = chat.gpt_get_trainings(trainings_dict, prompt_trainings)

    return schemas.TimetableData(**timetable_dict), recipes, trainings

