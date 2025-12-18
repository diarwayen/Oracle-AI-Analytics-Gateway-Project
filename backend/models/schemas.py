from pydantic import BaseModel
from typing import Any, Optional


class QueryRequest(BaseModel):
    """
    Kullanıcının doğal dilde sorduğu soruyu temsil eder.
    Örnek:
    {
      "user_question": "Son 30 günde en çok satan 10 ürünü getir"
    }
    """

    user_question: str


class APIResponse(BaseModel):
    """
    AI + Oracle hattından dönen standart cevabı temsil eder.
    """

    user_question: str
    generated_sql: Optional[str] = None
    explanation: Optional[str] = None
    data: Any


class ErrorResponse(BaseModel):
    """
    Hata durumlarında kullanılabilecek basit şema.
    (Şu an sadece dokümantasyon ve ileride kullanım için)
    """

    detail: str


