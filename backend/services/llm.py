from typing import TypedDict, Union, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from core.config import settings
import json

# 1. STATE TANIMI (Python 3.9 Uyumlu Hale Getirildi)
# "list | dict" yerine "Union[list, dict]" kullanıldı.
class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    # Union: Birden fazla tip alabilir (Liste, Sözlük, String veya None)
    query_result: Union[List[Any], Dict[str, Any], str, None]
    # Optional: String olabilir veya None olabilir
    error: Optional[str]
    attempts: int

# 2. MODEL TANIMI
print(f"--- LLM Modeli Başlatılıyor: {settings.LLM_MODEL} ---")
llm = ChatOllama(
    model=settings.LLM_MODEL,
    temperature=0,
    format="json",
    base_url=settings.OLLAMA_BASE_URL
)

# 3. NODE 1: SQL ÜRETİCİ
def generate_sql_node(state: AgentState):
    question = state["question"]
    schema = state["schema"]
    error = state.get("error")
    
    system_prompt = f"""Sen bir Oracle SQL uzmanısın. Şema: {schema}.
    Sadece JSON formatında cevap ver: {{"sql": "SELECT...", "explanation": "..."}}
    """
    
    user_content = f"Soru: {question}"
    
    if error:
        user_content += f"\n\nÖnceki denemende şu hatayı aldın, lütfen düzelt: {error}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    try:
        response = llm.invoke(messages)
        # JSON parse işlemi
        parsed = json.loads(response.content)
        sql = parsed.get("sql", "")
    except Exception as e:
        print(f"LLM Parse Hatası: {e}")
        sql = "ERROR_PARSING"
        
    # Python 3.9 TypedDict için return yapısı
    return {
        "sql_query": sql, 
        "attempts": state.get("attempts", 0) + 1
    }

# 4. NODE 2: SQL ÇALIŞTIRICI
def execute_sql_node(state: AgentState):
    # Burada döngüsel import (circular import) olmaması için import'u içeri aldık
    from services.oracle import OracleService
    
    sql = state["sql_query"]
    
    # Eğer önceki adımda SQL üretilemediyse hiç Oracle'a gitme
    if sql == "ERROR_PARSING" or not sql:
        return {"error": "SQL üretilemedi", "query_result": None}

    oracle = OracleService()
    
    try:
        oracle.connect()
        result = oracle.execute_query(sql)
        oracle.close()
        
        # OracleService hata sözlüğü döndürdüyse
        if isinstance(result, dict) and "error" in result:
             return {"error": result["error"], "query_result": None}
             
        return {"query_result": result, "error": None}
        
    except Exception as e:
        return {"error": str(e), "query_result": None}

# 5. KENAR (EDGE) MANTIĞI
def should_continue(state: AgentState) -> str:
    error = state.get("error")
    attempts = state.get("attempts", 0)
    
    if not error:
        return "end"
    
    if attempts >= 3:
        return "end"
        
    return "retry"

# 6. GRAFİK OLUŞTURMA
workflow = StateGraph(AgentState)

workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)

workflow.set_entry_point("generate_sql")

workflow.add_edge("generate_sql", "execute_sql")

workflow.add_conditional_edges(
    "execute_sql",
    should_continue,
    {
        "end": END,
        "retry": "generate_sql"
    }
)

app_graph = workflow.compile()

# DIŞARIYA AÇILAN FONKSİYON
def run_agent(user_question: str, schema_info: str):
    """
    Router'ın çağıracağı ana fonksiyon budur.
    """
    inputs = {
        "question": user_question, 
        "schema": schema_info, 
        "attempts": 0, 
        "error": None,
        "sql_query": "",
        "query_result": None
    }
    
    # Grafiği çalıştır
    result = app_graph.invoke(inputs)
    
    return {
        "sql": result.get("sql_query"),
        "data": result.get("query_result"),
        "error": result.get("error")
    }