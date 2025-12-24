from pydantic import BaseModel
from typing import Any, Optional


class UserQuestion(BaseModel):

    user_question: str


class APIResponse(BaseModel):

    user_question: str
    generated_sql: Optional[str] = None
    explanation: Optional[str] = None
    data: Any


class ErrorResponse(BaseModel):

    detail: str