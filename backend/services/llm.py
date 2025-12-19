from typing import TypedDict, Union, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from core.config import settings
import json
import re

# 1. STATE TANIMI
class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    query_result: Union[List[Any], Dict[str, Any], str, None]
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
    
    # PROMPT: Örnekli anlatım (Few-Shot) ekledik
    system_prompt = f"""Sen uzman bir Oracle SQL veritabanı yöneticisisin.
    
    VERİTABANI ŞEMASI:
    {schema}
    
    KURALLAR:
    1. Sadece JSON formatında cevap ver: {{"sql": "SELECT...", "explanation": "..."}}
    2. 'SELECT TOP 1' KULLANMA. Oracle bunu desteklemez.
    3. 'LIMIT' KULLANMA.
    4. Satır sınırlamak için SONA 'FETCH FIRST 1 ROWS ONLY' ekle.
    
    DOĞRU ÖRNEK:
    SELECT urun_adi, fiyat FROM urunler ORDER BY fiyat DESC FETCH FIRST 1 ROWS ONLY
    
    YANLIŞ ÖRNEK (BUNLARI YAPMA):
    SELECT TOP 1 urun_adi... (YANLIŞ)
    SELECT urun_adi... LIMIT 1 (YANLIŞ)
    """
    
    user_content = f"Soru: {question}"
    
    if error:
        user_content += f"\n\nÖnceki SQL hatalıydı: {error}. Lütfen Oracle 21c syntax'ına uygun düzelt."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    try:
        response = llm.invoke(messages)
        parsed = json.loads(response.content)
        raw_sql = parsed.get("sql", "")
        
        # --- ZORLA DÜZELTME (REGEX) ---
        clean_sql = raw_sql.replace(";", "").replace('"', "").strip()
        
        # 1. Markdown temizliği
        clean_sql = clean_sql.replace("```sql", "").replace("```", "")
        
        # 2. LIMIT'i zorla FETCH FIRST'e çevir (Model dinlemezse biz düzeltiriz)
        # "LIMIT 5" -> "FETCH FIRST 5 ROWS ONLY"
        clean_sql = re.sub(r'LIMIT\s+(\d+)', r'FETCH FIRST \1 ROWS ONLY', clean_sql, flags=re.IGNORECASE)
        
        # 3. TOP N yapısını temizle (Basit bir yaklaşımla TOP kelimesini uçuruyoruz, ORDER BY varsa çalışır)
        # SELECT TOP 1 col... -> SELECT col...
        # Bu biraz riskli ama ORA-00923'ü genelde bu çözer.
        if "TOP " in clean_sql.upper():
             clean_sql = re.sub(r'SELECT\s+TOP\s+\d+\s+', 'SELECT ', clean_sql, flags=re.IGNORECASE)
        
        print(f"DEBUG - Üretilen SQL: {clean_sql}") # Konsolda görelim
        
    except Exception as e:
        print(f"LLM Parse Hatası: {e}")
        clean_sql = "ERROR_PARSING"
        
    return {
        "sql_query": clean_sql, 
        "attempts": state.get("attempts", 0) + 1
    }

# 4. NODE 2: SQL ÇALIŞTIRICI
def execute_sql_node(state: AgentState):
    from services.oracle import OracleService
    
    sql = state["sql_query"]
    print(f"--- SQL Çalıştırılıyor: {sql} ---") # LOG EKLENDİ
    
    if sql == "ERROR_PARSING" or not sql:
        return {"error": "SQL üretilemedi", "query_result": None}

    oracle = OracleService()
    
    try:
        oracle.connect()
        result = oracle.execute_query(sql)
        oracle.close()
        
        if isinstance(result, dict) and "error" in result:
             return {"error": result["error"], "query_result": None}
             
        return {"query_result": result, "error": None}
        
    except Exception as e:
        return {"error": str(e), "query_result": None}

# 5. KENAR MANTIĞI
def should_continue(state: AgentState) -> str:
    error = state.get("error")
    attempts = state.get("attempts", 0)
    
    if not error:
        return "end"
    
    if attempts >= 3:
        return "end"
        
    return "retry"

# 6. GRAFİK
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
    inputs = {
        "question": user_question, 
        "schema": schema_info, 
        "attempts": 0, 
        "error": None,
        "sql_query": "",
        "query_result": None
    }
    
    # Döngü limitini artırdık
    result = app_graph.invoke(inputs, config={"recursion_limit": 15})
    
    return {
        "sql": result.get("sql_query"),
        "data": result.get("query_result"),
        "error": result.get("error"),
        "explanation": f"SQL: {result.get('sql_query')}"
    }