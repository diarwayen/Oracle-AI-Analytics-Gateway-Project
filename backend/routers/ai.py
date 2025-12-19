from fastapi import APIRouter, HTTPException, Depends, Security
from models.schemas import UserQuestion, APIResponse
# ÖNEMLİ: Sadece run_agent import ediliyor, llm_service SİLİNDİ.
from services.llm import run_agent 
from services.oracle import OracleService
from services.logger import logger as audit_logger
from core.security import get_api_key
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(get_api_key)]
)

# --- 1. GERÇEK FONKSİYON (Veritabanı Bağlantılı LangGraph) ---
@router.post("/ask-ai", response_model=APIResponse)
def ask_ai_endpoint(request: UserQuestion):
    oracle = None
    generated_sql = None
    data = None
    error_msg = None
    success = False
    explanation = None

    try:
        # 1. Oracle Şemasını Çek (Graph'a vermek için)
        oracle = OracleService()
        oracle.connect()
        schema_info = oracle.get_schema_info()
        oracle.close()
        
        logger.info(f"Kullanıcı Sorusu: {request.user_question}")
        
        # 2. LANGGRAPH AJANINI ÇALIŞTIR
        graph_result = run_agent(request.user_question, schema_info)
        
        # Sonuçları al
        generated_sql = graph_result.get("sql")
        data = graph_result.get("data")
        error_from_agent = graph_result.get("error")

        # Ajan başarısız olduysa
        if error_from_agent:
            raise ValueError(f"AI işlemi başarısız oldu: {error_from_agent}")

        if not generated_sql:
             raise ValueError("AI SQL üretemedi.")
        
        explanation = "LangGraph ajanı tarafından optimize edilerek çalıştırıldı."
        success = True
        logger.info(f"Başarılı İşlem! SQL: {generated_sql}")

        return APIResponse(
            user_question=request.user_question,
            generated_sql=generated_sql,
            explanation=explanation,
            data=data,
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Hata oluştu: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
        
    finally:
        # MongoDB Loglama
        row_count = len(data) if isinstance(data, list) else 0
        audit_logger.log_interaction(
            user_question=request.user_question,
            sql_generated=generated_sql,
            success=success,
            error_message=error_msg,
            row_count=row_count
        )

# --- 2. TEST FONKSİYONU (LangGraph Uyumlu Hale Getirildi) ---
@router.post("/test-only-llm")
async def test_llm_connection(request: UserQuestion):
    """
    Bu fonksiyon Oracle'a bağlanmaz, sahte şema ile ajanı test eder.
    """
    try:
        dummy_schema = """
        Tablo: SATISLAR
        Kolonlar: URUN_ADI (VARCHAR), MIKTAR (NUMBER), TARIH (DATE)
        """
        
        logger.info(f"TEST: AI'ya soruluyor: {request.user_question}")
        
        # Ajanı çalıştır (Oracle bağlantısı yapmaya çalışacak ama dummy_schema olduğu için 
        # sql üretecek, execute adımında hata alsa bile SQL'i göreceğiz)
        graph_result = run_agent(request.user_question, dummy_schema)
        
        return {
            "durum": "connected",
            "mesaj": "Grafana and AI are connected via LangGraph.",
            "ai_output": graph_result
        }
            
    except Exception as e:
        logger.error(f"TEST HATASI: {str(e)}")
        return {
            "durum": "HATA ❌",
            "hata": str(e),
            "trace": traceback.format_exc()
        }

@router.get("/mock-test")
async def mock_test():
    return [
        {"id": 1, "product": "Klavye", "sales": 150, "status": "OK"},
        {"id": 2, "product": "Mouse", "sales": 200, "status": "OK"},
        {"id": 3, "product": "Monitor", "sales": 80, "status": "Warning"}
    ]