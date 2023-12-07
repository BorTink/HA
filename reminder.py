from datetime import date, datetime, timedelta
import os
import requests

from dotenv import load_dotenv
from loguru import logger

from app.handlers import bot
import dal

load_dotenv()
BOT_TOKEN = os.getenv('TOKEN')


class Reminder:
    def __init__(self):
        self.reminder_trainings = None
        self.url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async def remind(self, training):
        training_date = training.created_date.date() + timedelta(
            days=training.day)
        current_time = datetime.today()
        current_date = date.today()

        if current_date == training_date and any([
            current_time.hour == 16 and current_time.minute == 10,
            current_time.hour == 18 and current_time.minute == 59,
            current_time.hour == 19 and current_time.minute == 1
        ]
        ):
            resp = requests.post(self.url, params={
                "text": "🌆Добрый вечер! Напоминаем, что завтра у вас запланирована тренировка. "
                        "Не забудьте отдохнуть и как следует выспаться перед занятием.",
                "chat_id": training.user_id})

            if not resp.json()['ok']:
                logger.info(
                    f'Произошла ошибка при отправке напоминания пользователю {training.user_id} - {resp.json()} '
                    f'Отправляем через send_message'
                )
                await bot.send_message(training.user_id,
                                       "🌆Добрый вечер! Напоминаем, что завтра у вас запланирована тренировка. "
                                       "Не забудьте отдохнуть и как следует выспаться перед занятием."
                                       )
            else:
                logger.info(f'Было отправлено напоминание пользователю {training.user_id} - {resp.json()}')

        elif current_date == training_date and any([
            current_time.hour == 10 and current_time.minute == 0,
            current_time.hour == 9 and current_time.minute == 59,
            current_time.hour == 10 and current_time.minute == 1
        ]
        ):
            resp = requests.post(self.url, params={
                "text": "🏙Добрый день! Напоминаем, что сегодня у вас состоится тренировка. "
                        "Желаем продуктивного занятия!",
                "chat_id": training.user_id})
            logger.info(f'Было отправлено напоминание пользователю {training.user_id} - {resp.json()}')

            if not resp.json()['ok']:
                logger.info(
                    f'Произошла ошибка при отправке напоминания пользователю {training.user_id} - {resp.json()} '
                    f'Отправляем через send_message'
                )
                await bot.send_message(training.user_id,
                                       "🏙Добрый день! Напоминаем, что сегодня у вас состоится тренировка. "
                                       "Желаем продуктивного занятия!",
                                       )
            else:
                logger.info(f'Было отправлено напоминание пользователю {training.user_id} - {resp.json()}')

        elif current_date == training_date + timedelta(days=1) and any([
            current_time.hour == 10 and current_time.minute == 0,
            current_time.hour == 9 and current_time.minute == 59,
            current_time.hour == 10 and current_time.minute == 1
        ]
        ):
            resp = requests.post(self.url, params={
                "text": "‼️Добрый день! Похоже, вы пропустили свою прошлую тренировку(\n"
                        "Помните, что без регулярности и последовательности занятия не дадут нужных результатов. "
                        "Выполните пропущенную тренировку и возвращайтесь в привычный ритм!",
                "chat_id": training.user_id})

            if not resp.json()['ok']:
                logger.info(
                    f'Произошла ошибка при отправке напоминания пользователю {training.user_id} - {resp.json()} '
                    f'Отправляем через send_message'
                )
                await bot.send_message(training.user_id,
                                       "‼️Добрый день! Похоже, вы пропустили свою прошлую тренировку(\n"
                                       "Помните, что без регулярности и последовательности занятия не дадут нужных "
                                       "результатов."
                                       "Выполните пропущенную тренировку и возвращайтесь в привычный ритм!",
                                       )
            else:
                logger.info(f'Было отправлено напоминание пользователю {training.user_id} - {resp.json()}')

        elif current_date == training_date + timedelta(days=2) and any([
            current_time.hour == 10 and current_time.minute == 0,
            current_time.hour == 9 and current_time.minute == 59,
            current_time.hour == 10 and current_time.minute == 1
        ]
        ):
            notification_text = ('‼️Добрый день! У вас есть 1 невосполненный пропуск. '
                                 'Выполните свою тренировку, чтобы продолжить заниматься в привычном режиме.')
            if (
                    await dal.User.check_if_subscribed_by_user_id(training.user_id)
                    or not
                    await dal.User.check_if_rebuilt_by_user_id(training.user_id)
            ):
                notification_text += 'Если вы хотите изменить расписание / количество тренировок, обновите свои данные.'

            resp = requests.post(self.url, params={
                "text": notification_text,
                "chat_id": training.user_id})

            if not resp.json()['ok']:
                logger.info(
                    f'Произошла ошибка при отправке напоминания пользователю {training.user_id} - {resp.json()} '
                    f'Отправляем через send_message'
                )
                await bot.send_message(training.user_id,
                                       notification_text
                                       )
            else:
                logger.info(f'Было отправлено напоминание пользователю {training.user_id} - {resp.json()}')

    async def execute(self):
        self.reminder_trainings = await dal.Trainings.get_all_active_trainings_with_dates()
        if self.reminder_trainings:
            for training in self.reminder_trainings:
                await self.remind(training)

    async def __call__(self, *args, **kwargs):
        await self.execute()
