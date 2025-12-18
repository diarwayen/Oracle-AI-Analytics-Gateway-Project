from fastapi import APIRouter, HTTPException, Depends
from models.schemas import QueryRequest, APIResponse
from services import llm, oracle, logger
from core.security import get_api_key

# Router tanımla (Küçük bir app gibi davranır)
# Tüm endpoint'ler için API key kontrolü uygula
router = APIRouter(
    dependencies=[Depends(get_api_key)]
)

@router.post("/ask-ai", response_model=APIResponse)
def ask_ai_endpoint(request: QueryRequest):
    """
    Kullanıcının doğal dilde sorduğu soruyu alır,
    LLM ile SQL üretir ve Oracle veritabanında çalıştırır.
    Sonucu standart APIResponse formatında döner.
    """
    try:
        # 1) LLM'den SQL üret
        llm_result = llm.generate_sql_from_text(request.user_question)
        if not llm_result:
            raise ValueError("AI hata verdi veya boş cevap döndü.")

        sql = llm_result.get("sql")
        explanation = llm_result.get("aciklama")

        if not sql:
            raise ValueError("AI geçerli bir SQL üretemedi.")

        # 2) Oracle'da sorguyu çalıştır
        data = oracle.run_query(sql)

        # Hata nesnesi döndüyse onu fırlat
        if isinstance(data, dict) and data.get("error"):
            raise ValueError(data["error"])

        # 3) Loglama
        row_count = len(data) if isinstance(data, list) else 0
        logger.logger.log_interaction(
            request.user_question,
            sql,
            True,
            row_count=row_count,
        )

        # 4) Standart response
        return APIResponse(
            user_question=request.user_question,
            generated_sql=sql,
            explanation=explanation,
            data=data,
        )

    except Exception as e:
        # Başarısız denemeyi logla
        logger.logger.log_interaction(
            request.user_question,
            None,
            False,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))