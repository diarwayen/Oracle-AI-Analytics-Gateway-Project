from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, APIResponse
from services import llm, oracle, logger

# Router tanımla (Küçük bir app gibi davranır)
router = APIRouter()

@router.post("/ask-ai", response_model=APIResponse)
def ask_ai_endpoint(request: QueryRequest):
    # ... (Main.py içindeki kodun AYNISI buraya gelecek) ...
    # Kodu buraya kopyala-yapıştır yapabilirsin.
    # Tek fark: @app.post değil @router.post olacak.
    
    # Örnek akış (kısaltılmış):
    try:
        llm_result = llm.generate_sql_from_text(request.user_question)
        if not llm_result: raise ValueError("AI hata verdi")
        
        sql = llm_result.get("sql")
        data = oracle.run_query(sql)
        
        logger.logger.log_interaction(request.user_question, sql, True, row_count=len(data))
        
        return {
            "user_question": request.user_question,
            "generated_sql": sql,
            "explanation": llm_result.get("aciklama"),
            "data": data
        }
    except Exception as e:
        logger.logger.log_interaction(request.user_question, None, False, str(e))
        raise HTTPException(status_code=500, detail=str(e))