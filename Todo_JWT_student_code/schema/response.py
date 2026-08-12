from datetime import datetime
from pydantic import BaseModel


class TodoResponse(BaseModel):
    id: int
    title: str
    is_done: bool
    user_id: int | None


class UserSignUpResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
