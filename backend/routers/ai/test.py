from fastapi import APIRouter
from models.schemas import UserQuestion
from services.llm import run_agent
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Test"])


@router.post("/test-only-llm")
async def test_llm_connection(request: UserQuestion):
    try:
        dummy_schema = """
        Tablo: SATISLAR
        Kolonlar:   URUN_ADI (VARCHAR),
                    MIKTAR (NUMBER),
                    TARIH (DATE)
        """

        logger.info(f"TEST: AI'ya soruluyor: {request.user_question}")
        graph_result = run_agent(request.user_question, dummy_schema)

        return {
            "durum": "connected",
            "mesaj": "Grafana and AI are connected via LangGraph.",
            "ai_output": graph_result,
        }

    except Exception as e:
        logger.error(f"TEST HATASI: {str(e)}")
        return {
            "durum": "HATA ",
            "hata": str(e),
            "trace": traceback.format_exc(),
        }


@router.get("/mock-test")
async def mock_test():
    return [
        {"id": 1, "product": "Klavye", "sales": 150, "status": "OK"},
        {"id": 2, "product": "Mouse", "sales": 200, "status": "OK"},
        {"id": 3, "product": "Monitor", "sales": 80, "status": "Warning"},
    ]



