from typing import Optional

from pydantic import BaseModel, field_validator
from loguru import logger


class PromptData(BaseModel):
    tg_id: int
    gender: str
    age: int
    height: int
    weight: int
    gym_experience: str

    squats_results: Optional[int]
    bench_results: Optional[int]
    deadlift_results: Optional[int]

    goals: str
    intensity: str
    health_restrictions: str
    allergy: str
    times_per_week: int

    rebuilt: bool
    subscribed: bool

    @field_validator('squats_results', 'bench_results', 'deadlift_results', mode='before')
    def validate_results(cls, value):
        if value is None:
            return None
        elif str(value).isdigit():
            return int(value)
        elif str(value) == 'none':
            return None
        else:
            logger.error(f'Результат троеборья - строка - {value}')
            raise Exception


class TimetableData(BaseModel):
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str
