from fastapi import APIRouter, Depends, HTTPException, Security
from typing import List, Dict, Any
from services.llm import llm_service 
from services.oracle import OracleService
from models.schemas import UserQuestion
from core.security import get_api_key
import logging

# Loglama
logger = logging.getLogger(__name__)

router = APIRouter()

# --- 1. GERÇEK FONKSİYON ---
@router.post("/ask-ai")
async def ask_ai(
    request: UserQuestion, 
    api_key: str = Security(get_api_key)
):
    try:
        # Oracle Bağlantısı
        oracle = OracleService()
        oracle.connect()
        schema_info = oracle.get_schema_info()
        
        # AI Çağrısı
        logger.info(f"AI'ya soruluyor: {request.user_question}")
        ai_response = llm_service.get_sql(request.user_question, schema_info)
        
        generated_sql = ai_response.get("sql", "")
        explanation = ai_response.get("explanation", "")
        
        # SQL Çalıştırma
        data = []
        if generated_sql and generated_sql != "ERROR":
            data = oracle.execute_query(generated_sql)
            
        oracle.close()
        
        return {
            "user_question": request.user_question,
            "generated_sql": generated_sql,
            "explanation": explanation,
            "data": data
        }

    except Exception as e:
        logger.error(f"Hata: {str(e)}")
        return {
            "error": "İşlem hatası",
            "detail": str(e)
        }

