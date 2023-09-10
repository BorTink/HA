from pydantic import BaseModel


class PromptData(BaseModel):
    sex: str
    age: str
    height: str
    weight: str
    illnesses: str
    drugs: str
    level_of_fitness: str
    goal: str
    result: str
    allergy: str
    diet: str
    number_of_meals: str
    trainings_per_week: str
    train_time_amount: str
    gym_access: str
    gym_equipment: str


class TimetableData(BaseModel):
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str
    sunday: str
