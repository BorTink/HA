from pydantic import BaseModel


class Meal(BaseModel):
    meal_plan: str
    day: int
