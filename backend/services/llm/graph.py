from typing import TypedDict, Union, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re
from typing import Callable

from services.llm.model import get_llm
from services.llm.prompts import build_system_prompt, build_user_content
from services.db.base import QueryExecutor


class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    query_result: Union[List[Any], Dict[str, Any], str, None]
    error: Optional[str]
    attempts: int


def generate_sql_node(state: AgentState) -> Dict[str, Any]:
    question = state["question"]
    schema = state["schema"]
    error = state.get("error")

    system_prompt = build_system_prompt(schema)
    user_content = build_user_content(question, error)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        llm = get_llm()
        response = llm.invoke(messages)
        parsed = json.loads(response.content)
        raw_sql = parsed.get("sql", "")

        # --- ZORLA DÜZELTME (REGEX) ---
        clean_sql = raw_sql.replace(";", "").replace('"', "").strip()

        # 1. Markdown temizliği
        clean_sql = clean_sql.replace("```sql", "").replace("```", "")

        # 2. LIMIT'i zorla FETCH FIRST'e çevir
        clean_sql = re.sub(r"LIMIT\s+(\d+)", r"FETCH FIRST \1 ROWS ONLY", clean_sql, flags=re.IGNORECASE)

        # 3. TOP N temizliği
        if "TOP " in clean_sql.upper():
            clean_sql = re.sub(r"SELECT\s+TOP\s+\d+\s+", "SELECT ", clean_sql, flags=re.IGNORECASE)

        print(f"DEBUG - Üretilen SQL: {clean_sql}")

    except Exception as e:
        print(f"LLM Parse Hatası: {e}")
        clean_sql = "ERROR_PARSING"

    return {
        "sql_query": clean_sql,
        "attempts": state.get("attempts", 0) + 1,
    }


def make_execute_sql_node(executor_factory: Callable[[], QueryExecutor]):
    def execute_sql_node(state: AgentState) -> Dict[str, Any]:
        sql = state["sql_query"]
        print(f"--- SQL Çalıştırılıyor: {sql} ---")

        if sql == "ERROR_PARSING" or not sql:
            return {"error": "SQL üretilemedi", "query_result": None}

        executor = executor_factory()

        try:
            executor.connect()
            result = executor.execute_query(sql)
            executor.close()

            if isinstance(result, dict) and "error" in result:
                return {"error": result["error"], "query_result": None}

            return {"query_result": result, "error": None}

        except Exception as e:
            return {"error": str(e), "query_result": None}

    return execute_sql_node


def should_continue(state: AgentState) -> str:
    error = state.get("error")
    attempts = state.get("attempts", 0)

    if not error:
        return "end"

    if attempts >= 3:
        return "end"

    return "retry"


def build_app_graph(executor_factory: Callable[[], QueryExecutor]):
    workflow = StateGraph(AgentState)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", make_execute_sql_node(executor_factory))
    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_conditional_edges(
        "execute_sql",
        should_continue,
        {
            "end": END,
            "retry": "generate_sql",
        },
    )
    return workflow.compile()

