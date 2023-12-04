from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator
from loguru import logger


class ReminderTraining(BaseModel):
    user_id: int
    created_date: datetime
    day: int
    chat_id: int


class BaseExercise(BaseModel):
    name: str
    link: str
