import re

import openai
from loguru import logger

import dal
import schemas

openai.api_key = "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"


class ChatGPT:
    def __init__(self):
        openai.api_key = "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"
        self.starting_message = {"role": "system", "content":
            """
            You are a fitness trainer capable of creating a workout program in gym.
            """
        }
        self.messages = [
            self.starting_message
        ]

    def chat(self, message):
        self.messages.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            max_tokens=3100
        )
        return response["choices"][0]["message"].content

    def gpt_create_timetable(self, message):
        self.messages = [
            self.starting_message,
            {"role": "user", "content": message}
        ]
        words = len(self.messages[0]["content"].split()) + len(self.messages[1]["content"].split())
        logger.info(f'Длина промпта для расписания '
                    f'- {words} слов, т.е. примерно {words*2} токенов')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            max_tokens=3000
        )
        self.messages = [
            self.starting_message,
            {"role": "assistant", "content": response["choices"][0]["message"].content}
        ]
        words_answer = len(self.messages[1]["content"].split())
        logger.info(f'Длина расписания '
                    f'- {words_answer} слов, т.е. примерно {words_answer*2} токенов. '
                    f'В сумме вышло {words_answer*2 + words*2} токенов')
        logger.info(f'Все расписание - {response["choices"][0]["message"]["content"]}')

        return response["choices"][0]["message"]['content']


async def fill_prompt(prompt_data: schemas.PromptData):
    prompt_text = f"""
    Make a full week plan with training days and rest days for the next workouts in the format of 
    "Exercise - exact weight of equipment - number of sets - number of repetitions or time required for the exercise - rest between repetitions" 
    without other words based on user information, basic workout rules and practices of top athletes. 
    In your plan you must separate different muscle groups to different days. Workout time must be 60-90 minutes. Add warm-up before every training. 
    Use only top 20 basic exercises, available in every gym, excluding any type of french press. 
    In exercises instead of an empty barbell recommend at least 30 kg of weight. 
    Our user wants to increase his body mass, so you should make a combination of 70% powerlifting and 30% bodybuilding in your plan and 
    make 4-6 repeats per set of primary exercises with 8-10 repeats per set of auxiliary exercises in your plan.
    Your plan should have 90-120 repeats of exercises for large muscle groups a week.
    If you add deadlift to your plan, remind user to do hyperextension before it to warm up his back.
    Translate your answer to Russian appropriately to gym context, but translate 'deadlift' as 'Становая тяга (рекомендуется сделать 1 подход гиперэкстензии перед началом подходов)'.
    When writing the plan, strictly follow the example format below.
    
    User information:
    
    Gender - Male
    Age - {prompt_data.age} y. o.
    Height - {prompt_data.height} cm
    Weight - {prompt_data.weight} kg
    Previous gym experience - {prompt_data.gym_experience}
    Desired goals - {prompt_data.goals}
    Desired intensity - {prompt_data.intensity}
    Health restrictions - {prompt_data.health_restrictions}
    Trainings per week - {prompt_data.times_per_week}
    
    Current maximum results in exercises (kg): 
    squats - {prompt_data.squats_results}, 
    bench press - {prompt_data.bench_results}, 
    deadlift - {prompt_data.deadlift_results}. (weight with barbell 20 kg).
    
    EXAMPLE:
    {{
    День 1: ....
    
    Разминка: 10-15 минут (и краткое описание что сделать)
    (Название упражнения) - ... кг,.. подходов , ..  повторений, отдых .. минуты
    
    День 2: ....
    
    Разминка: 10-15 минут (и краткое описание что сделать)
    (Название упражнения) - ... кг,.. подходов , ..  повторений, отдых .. минуты
    
    ...
    END
    }}
    """

    chat = ChatGPT()

    timetable_days = chat.gpt_create_timetable(prompt_text).split('День')
    training_days = []
    for i in range(len(timetable_days)):
        logger.info(f'День {i+1} - {timetable_days[i]}')
        if len(timetable_days[i].split()) < 12:
            if i == 0:
                continue
            training_days.append('Отдых')
        else:
            if i == len(timetable_days)-1:
                training_days.append('\n\n'.join(timetable_days[i].split('\n\n')[:-1]))
            else:
                training_days.append('\n\n'.join(timetable_days[i].split('\n\n')))

    return training_days
