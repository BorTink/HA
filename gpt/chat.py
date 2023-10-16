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
            Separate different muscle groups to different days. 
            Workout time must be 60-90 minutes. 
            Please only write a plan for the next workouts in the format of 
            "Exercise - exact weight of equipment - number of sets - number of repetitions or time required for the exercise, rest between every approaches" 
            without other words based on user information, basic workout rules and practices of top athletes. 
            Add warm-up before every training. 
            Use only top 20 basic exercises, available in every gym, excluding any type of french press. 
            In exercises instead of empty barbell recommend at least 30 kg of weight. 
            Person wants to up his body mass, you should make a combination of 70% powerlifting and 30% bodybuilding in your plan, 
            do combination of basic exercises with 4-6 approaches maximum weight and auxiliary 8-10 approaches. 
            Basic exercises for a large group of muscles need to do from 90-120 approaches a week. 
            Translate your answer to Russian. 
            Make a full week plan with training days and rest days.
            Remember that 'deadlift' is 'становая тяга'.
            
            EXAMPLE:
            День 1: '....'
            
            Разминка: 10-15 минут (и краткое описание что сделать)
            Упражнение - ... кг,.. подходов , ..  повторений, отдых .. минуты
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
        logger.info(f'Длина промпта для расписания '
                    f'- {len(self.messages[0]["content"].split()) + len(self.messages[1]["content"].split())} слов')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
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


async def fill_prompt(prompt_data: schemas.PromptData):
    prompt_text = f"""
    Gender - Male
    Age - {prompt_data.age} y. o.
    Height - {prompt_data.height} cm
    Weight - {prompt_data.weight} kg
    Previous gym experience - {prompt_data.gym_experience}
    Desired goals - {prompt_data.goals}
    Desired intensity - {prompt_data.intensity}
    Health restrictions - {prompt_data.health_restrictions}
    Trainings day want a week - {prompt_data.times_per_week}
    
    Current maximum results in exercises (kg): 
    squats - {prompt_data.squats_results}, 
    bench press - {prompt_data.bench_results}, 
    deadlift - {prompt_data.deadlift_results}. (weight with barbell 20 kg).
    """

    chat = ChatGPT()

    timetable_days = chat.gpt_create_timetable(prompt_text).split('День')
    training_days = []
    for i in range(timetable_days):
        if len(timetable_days[i].split()) < 12:
            training_days[i] = 'Отдых'
        else:
            training_days[i] = '\n\n'.join(timetable_days[i].split('\n\n')[1:-1])

    return training_days
