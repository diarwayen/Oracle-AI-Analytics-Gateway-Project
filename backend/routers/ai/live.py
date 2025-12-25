from fastapi import APIRouter, HTTPException, Depends
from models.schemas import UserQuestion, APIResponse
from services.llm import run_agent
from services.logger import logger as audit_logger
from core.deps import get_oracle_service, get_executor_factory
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ask-ai", response_model=APIResponse)
def ask_ai_endpoint(
    request: UserQuestion,
    oracle=Depends(get_oracle_service),
    executor_factory=Depends(get_executor_factory),
):
    generated_sql = None
    data = None
    error_msg = None
    success = False
    explanation = None

    try:
        schema_info = oracle.get_schema_info()

        logger.info(f"Kullanıcı Sorusu: {request.user_question}")

        graph_result = run_agent(
            request.user_question,
            schema_info,
            executor_factory=executor_factory,
        )

        generated_sql = graph_result.get("sql")
        data = graph_result.get("data")
        error_from_agent = graph_result.get("error")

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
        row_count = len(data) if isinstance(data, list) else 0
        audit_logger.log_interaction(
            user_question=request.user_question,
            sql_generated=generated_sql,
            success=success,
            error_message=error_msg,
            row_count=row_count,
        )




