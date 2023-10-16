from pydantic import BaseModel


class PromptData(BaseModel):
    tg_id: int
    gender: str
    age: int
    height: int
    weight: int
    gym_experience: str

    squats_results: str
    bench_results: str
    deadlift_results: str

    goals: str
    intensity: str
    health_restrictions: str
    times_per_week: int


class TimetableData(BaseModel):
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str
