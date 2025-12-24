from langchain_ollama import ChatOllama
from core.config import settings

_llm = None


def get_llm() -> ChatOllama:
    """Return a singleton ChatOllama client."""
    global _llm
    if _llm is None:
        print(f"--- LLM Modeli Başlatılıyor: {settings.LLM_MODEL} ---")
        _llm = ChatOllama(
            model=settings.LLM_MODEL,
            temperature=0,
            format="json",
            base_url=settings.OLLAMA_BASE_URL,
        )
    return _llm

