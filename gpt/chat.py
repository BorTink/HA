import re
import os
import pathlib

import openai
import tiktoken
from loguru import logger
from dotenv import load_dotenv

import schemas
from gpt.prompts import fill_man_lose_weight_prompt, fill_man_increase_weight_prompt, fill_woman_lose_weight_prompt

load_dotenv(str(pathlib.Path(__file__).parent.parent) + '/app/.env')
openai.api_key = os.getenv('GPT_API_TOKEN')


class ChatGPT:
    def __init__(self):
        self.starting_message = {"role": "system", "content":
            """
            You are a fitness trainer capable of creating a workout program in gym.
            """
        }
        self.messages = [
            self.starting_message
        ]
        self.client = openai.OpenAI(api_key=os.getenv('GPT_API_TOKEN'))
        self.assistant_id = 'asst_zrLHVX2RY9AjFjKy3f4pbYh6'
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
        return response["choices"][0]["message"].content

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
        answer = response["choices"][0]["message"].content

        self.messages = [
            self.starting_message,
            {"role": "assistant", "content": answer}
        ]

        answer_num_tokens = len(encoding.encode(answer))
        logger.info(f'Длина расписания '
                    f'- {answer_num_tokens} токенов. '
                    f'В сумме вышло {prompt_num_tokens + answer_num_tokens} токенов')

        logger.info(f'Все расписание - {answer}')

        return response["choices"][0]["message"]['content']


async def fill_prompt(prompt_data: schemas.PromptData, client_changes=None):
    if prompt_data.gender == 'Женский':
        prompt_text = await fill_woman_lose_weight_prompt(prompt_data, client_changes)
    else:
        if ' '.join(prompt_data.goals.split()[:2]) == "muscle gain.":
            prompt_text = await fill_man_increase_weight_prompt(prompt_data, client_changes)
        else:
            prompt_text = await fill_man_lose_weight_prompt(prompt_data, client_changes)

    chat = ChatGPT()
    gpt_timetable = await chat.gpt_create_timetable(prompt_text)
    timetable_days = re.split(r'День \d+:|День \d+и', gpt_timetable)
    training_days = []
    for i in range(len(timetable_days)):
        logger.info(f'День {i+1} - {timetable_days[i]}')
        if len(timetable_days[i].split()) < 12:
            if i == 0:
                continue
            training_days.append('Отдых\n\n')
        else:
            if i == len(timetable_days)-1:
                training_days.append('\n\n'.join(timetable_days[i].split('\n\n')[:-1]))
            else:
                training_days.append('\n\n'.join(timetable_days[i].split('\n\n')))

    return training_days
