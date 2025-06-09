from pydantic import BaseModel


class Criteria(BaseModel):
    id: str
    question: str
    weight: float


class UserResponse(BaseModel):
    id: str
    answer: bool
