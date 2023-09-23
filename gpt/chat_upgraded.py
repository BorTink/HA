import os
import re

from loguru import logger
from llama_index import SimpleDirectoryReader, VectorStoreIndex, LLMPredictor, PromptHelper, GPTVectorStoreIndex
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAIChat, OpenAI
import openai

import dal
import schemas

os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.getenv("OPENAI_API_KEY")

class UpgradedChatBot:
    def __init__(self):
        self.index = None
        self.construct_index("/home/boris/TelegramBots/Health_AI/docs")

    def construct_index(self, directory_path):
        max_input_size = 4096
        num_outputs = 300
        max_chunk_overlap = 0.8
        chunk_size_limit = 500

        prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

        llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-4", max_tokens=2500))

        documents = SimpleDirectoryReader(directory_path).load_data()

        self.index = GPTVectorStoreIndex.from_documents(
            documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper
        )
        self.index = self.index.as_query_engine()

    def chatbot(self, input_text):
        logger.info(type(self.index))
        response = self.index.query(input_text)
        return response.response


# index = construct_index("/home/boris/TelegramBots/Health_AI/docs")


async def fill_prompt(prompt_data: schemas.PromptData):
    prompt_text = f"""
Представь, что ты профессиональный тренер и нутрицолог. У тебя есть клиент, которому ты должен составить план питания и тренировок на каждый день недели (необходимо, чтобы на каждый день был разный план питания). Снизу есть данные клиента, на основе которых ты должен составить макимально унифицированный индивидуальный план тренировок и питания. Для тренировок обязательно подстраивай количество подходов и повторений под цель клиента, то есть, если набор мышечной массы, то нужно минимальное количество повторений (6-8) и тд. Разбей тренировки по группам мышц и начинай первую тренировку недели с верхней части тела. Также добавь примерное количество кг для каждого упражнения, учитывая средние способности при данных его анкеты и. План питания планируй в расчете на цели клиента. Выдай все в таком формате:

"Понедельник:
"день тренировки" (если она есть, если тренировки в этот день нет, то "день отдыха")
Тренировка:
Приседания со штангой: ...
Приемы пищи:
Завтрак:
...
Обед: ... и тд. (смотри, сколько приемов пищи пишет клиент)”

Нужно вывести расписание для каждого дня недели, нельзя объединять дни

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

    # timetable = chatbot(prompt_text)
    timetable = None
    logger.info(timetable)
    # timetable_list = re.split(
    #     'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday', timetable)
    #
    # prompt_recipes = f"""
    # Напиши мне подробные рецепты для приемов пищи, из этого расписания дня: {timetable_list[1]} Не давай дополнительных комментариев
    # """
    # recipes = chatbot(prompt_recipes)
    #
    # prompt_trainings = f"""
    # Напиши мне подробную текстовую инструкцию к тренировке из этого расписания дня: {timetable_list[1]}. Не давай дополнительных комментариев
    # """
    # trainings = chatbot(prompt_trainings)
    #
    # prompt_shopping_list = f"""
    # Я хочу пойти в магазин, чтобы у меня были продукты на неделю. Чтобы следовать плану питания. Сделай мне шоппинг лист на неделю с продуктами, которые необходимо купить для этих рецептов: {recipes}. Ранжируй продукты по категориям и времени хранения. По типу: хранятся 1-3 дня и тд. Для мяса напиши какой именно фрагмент тела надо купить. Не давай дополнительных комментариев
    # """
    # shopping_list = chatbot(prompt_shopping_list)
    #
    # timetable_dict = {
    #     'monday': timetable_list[1],
    #     'tuesday': timetable_list[2],
    #     'wednesday': timetable_list[3],
    #     'thursday': timetable_list[4],
    #     'friday': timetable_list[5],
    #     'saturday': timetable_list[6],
    #     'sunday': timetable_list[7],
    # }
    # return schemas.TimetableData(**timetable_dict), recipes, shopping_list, trainings

