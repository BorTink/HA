from pydantic import BaseModel


class PromptData(BaseModel):
    tg_id: int
    gender: str
    age: int
    height: int
    weight: int
    gym_experience: str
    goal: str
    time_to_reach: int
    intensity: str
    times_per_week: int
    health_restrictions: str
    squats_results: str
    bench_results: str
    deadlift_results: str


class TimetableData(BaseModel):
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str
