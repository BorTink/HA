import os
import json
import pathlib

import asyncio
import openai
import tiktoken
from loguru import logger
from dotenv import load_dotenv

import schemas
from gpt.prompts import fill_man_prompt, fill_woman_prompt, \
    fill_woman_prompt_next_week, fill_man_prompt_next_week, fill_man_meal_plan_prompt, fill_woman_meal_plan_prompt

load_dotenv(str(pathlib.Path(__file__).parent.parent) + '/app/.env')
openai.api_key = os.getenv('GPT_API_TOKEN')


class ChatGPT:
    def __init__(self, assistant_id):
        self.starting_message = {"role": "system", "content":
            """
            You are a fitness trainer capable of creating a workout program in gym.
            """
        }
        self.messages = [
            self.starting_message
        ]
        self.client = openai.OpenAI(api_key=os.getenv('GPT_API_TOKEN'))
        self.assistant_id = assistant_id
        self.thread = None
        self.run = None

    async def create_thread(self):
        self.thread = self.client.beta.threads.create()

    async def add_message(self, message):
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role='user',
            content=message
        )
        return message

    async def create_run(self):
        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant_id
        )
        return self.run

    async def get_run_status(self):
        status = self.client.beta.threads.runs.retrieve(
            thread_id=self.thread.id,
            run_id=self.run.id
        )
        return status

    async def get_all_messages(self):
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        return messages

    async def chat(self, message):
        self.messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=self.messages,
            max_tokens=3000,
            temperature=0.5
        )
        response = json.loads(response.model_dump_json())
        return response["choices"][0]['message']['content']

    async def gpt_create_timetable(self, message):
        self.messages = [
            self.starting_message,
            {"role": "user", "content": message}
        ]
        encoding = tiktoken.get_encoding('cl100k_base')
        prompt_num_tokens = len(encoding.encode(message))
        logger.info(f'Длина промпта для расписания '
                    f'- {prompt_num_tokens} токенов')

        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=self.messages,
            max_tokens=3000,
            temperature=0.5
        )
        response = json.loads(response.model_dump_json())
        answer = response["choices"][0]['message']['content']

        self.messages = [
            self.starting_message,
            {"role": "assistant", "content": answer}
        ]

        answer_num_tokens = len(encoding.encode(answer))
        logger.info(f'Длина расписания '
                    f'- {answer_num_tokens} токенов. '
                    f'В сумме вышло {prompt_num_tokens + answer_num_tokens} токенов')

        logger.info(f'Все расписание - {answer}')

        return response["choices"][0]['message']['content']


async def fill_prompt(prompt_data: schemas.PromptData, client_changes=None):
    global workout_gpt

    if prompt_data.gender == 'Женский':
        prompt_text = await fill_woman_prompt(prompt_data, client_changes)
        workout_gpt = ChatGPT(os.getenv('WOMAN_ASSISTANT_ID'))
    else:
        prompt_text = await fill_man_prompt(prompt_data, client_changes)
        workout_gpt = ChatGPT(os.getenv('MAN_ASSISTANT_ID'))

    await workout_gpt.create_thread()

    await workout_gpt.add_message(prompt_text)

    status = await workout_gpt.create_run()

    while status.status != 'completed':
        status = await workout_gpt.get_run_status()
        await asyncio.sleep(5)

    messages = await workout_gpt.get_all_messages()
    training = messages.data[0].content[0].text.value

    return training


async def fill_prompt_next_week(prompt_data: schemas.PromptData, trainings_prev_week, client_edits_next_week=None):
    if prompt_data.gender == 'Женский':
        prompt_text = await fill_woman_prompt_next_week(
            trainings_prev_week, client_edits_next_week
        )
        if 'workout_gpt' not in locals():
            workout_gpt = ChatGPT(os.getenv('WOMAN_ASSISTANT_ID'))
            await workout_gpt.create_thread()
    else:
        prompt_text = await fill_man_prompt_next_week(
            trainings_prev_week, client_edits_next_week
        )
        if 'workout_gpt' not in locals():
            workout_gpt = ChatGPT(os.getenv('MAN_ASSISTANT_ID'))
            await workout_gpt.create_thread()

    await workout_gpt.add_message(prompt_text)

    status = await workout_gpt.create_run()

    while status.status != 'completed':
        status = await workout_gpt.get_run_status()
        await asyncio.sleep(5)

    messages = await workout_gpt.get_all_messages()
    training = messages.data[0].content[0].text.value

    return training


async def fill_meal_plan_prompt(prompt_data: schemas.PromptData):
    global meal_gpt

    if prompt_data.gender == 'Женский':
        prompt_text = await fill_woman_meal_plan_prompt(prompt_data)
        meal_gpt = ChatGPT(os.getenv('WOMAN_ASSISTANT_ID'))
    else:
        prompt_text = await fill_man_meal_plan_prompt(prompt_data)
        meal_gpt = ChatGPT(os.getenv('MAN_ASSISTANT_ID'))

    await meal_gpt.create_thread()

    await meal_gpt.add_message(prompt_text)

    status = await meal_gpt.create_run()

    while status.status != 'completed':
        status = await meal_gpt.get_run_status()
        await asyncio.sleep(5)

    messages = await meal_gpt.get_all_messages()
    meal_plan = messages.data[0].content[0].text.value

    return meal_plan
