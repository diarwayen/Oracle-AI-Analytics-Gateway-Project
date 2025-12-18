# backend/routers/api.py - FİNAL VERSİYON (TEST VE GERÇEK BİR ARADA)

from fastapi import APIRouter, HTTPException, Depends, Security
from models.schemas import UserQuestion, APIResponse
from services.llm import llm_service
from services.oracle import OracleService
from core.security import get_api_key
import logging
import traceback

# Logger ayarı
logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(get_api_key)]
)

# --- 1. GERÇEK FONKSİYON (Veritabanı Bağlantılı) ---
@router.post("/ask-ai", response_model=APIResponse)
def ask_ai_endpoint(request: UserQuestion):
    """
    Kullanıcının doğal dilde sorduğu soruyu alır,
    LLM ile SQL üretir ve Oracle veritabanında çalıştırır.
    """
    oracle = None
    try:
        # Şemayı çekmek için önce Oracle'a bağlanalım
        oracle = OracleService()
        oracle.connect()
        schema_info = oracle.get_schema_info()
        
        logger.info(f"Kullanıcı Sorusu: {request.user_question}")
        
        # LLM Servisini Çağır
        llm_result = llm_service.get_sql(request.user_question, schema_info)
        
        if not llm_result:
             raise ValueError("AI boş cevap döndü.")

        sql = llm_result.get("sql")
        explanation = llm_result.get("explanation")

        if not sql or sql == "ERROR":
            raise ValueError(f"AI SQL üretemedi: {explanation}")

        # Oracle'da sorguyu çalıştır
        data = oracle.execute_query(sql)

        # Hata kontrolü
        if isinstance(data, dict) and data.get("error"):
            raise ValueError(data["error"])

        logger.info(f"Başarılı İşlem! SQL: {sql}")

        return APIResponse(
            user_question=request.user_question,
            generated_sql=sql,
            explanation=explanation,
            data=data,
        )

    except Exception as e:
        logger.error(f"Hata oluştu: {str(e)}")
        # Oracle hatası olsa bile kullanıcıya düzgün formatta dönelim
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if oracle:
            oracle.close()

# --- 2. TEST FONKSİYONU (Veritabanı olmadan test için - EKLENDİ ✅) ---
@router.post("/test-only-llm")
async def test_llm_connection(request: UserQuestion):
    """
    Bu fonksiyon Oracle'a bağlanmaz. Sadece AI'ın (TinyLlama) cevap verip vermediğini test eder.
    Grafana testi için bunu kullanabilirsin.
    """
    try:
        # Sahte bir şema uyduralım
        dummy_schema = """
        Tablo: SATISLAR
        Kolonlar: URUN_ADI (VARCHAR), MIKTAR (NUMBER), TARIH (DATE)
        """
        
        logger.info(f"TEST: AI'ya soruluyor: {request.user_question}")
        
        # AI'ya sor
        ai_response = llm_service.get_sql(request.user_question, dummy_schema)
        
        logger.info("TEST: AI Cevap verdi!")
        
        return {
            "durum": "connected",
            "mesaj": "Grafana and AI are connected.",
            "ai_generated_data": ai_response
        }
            
    except Exception as e:
        logger.error(f"TEST HATASI: {str(e)}")
        return {
            "durum": "HATA ❌",
            "hata": str(e),
            "trace": traceback.format_exc()
        }

# backend/routers/api.py içine eklenecek

@router.get("/mock-test")  # Başına /api otomatik gelecektir
async def mock_test():
    return [
        {"id": 1, "product": "Klavye", "sales": 150, "status": "OK"},
        {"id": 2, "product": "Mouse", "sales": 200, "status": "OK"},
        {"id": 3, "product": "Monitor", "sales": 80, "status": "Warning"}
    ]