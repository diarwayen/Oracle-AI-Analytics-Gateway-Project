from typing import Callable

from services.llm.graph import AgentState, build_app_graph
from services.db.base import QueryExecutor
from services.oracle import OracleService


def run_agent(
    user_question: str,
    schema_info: str,
    executor_factory: Callable[[], QueryExecutor] = OracleService,
):
    inputs: AgentState = {
        "question": user_question,
        "schema": schema_info,
        "attempts": 0,
        "error": None,
        "sql_query": "",
        "query_result": None,
    }

    graph = build_app_graph(executor_factory)
    result = graph.invoke(inputs, config={"recursion_limit": 15})

    return {
        "sql": result.get("sql_query"),
        "data": result.get("query_result"),
        "error": result.get("error"),
        "explanation": f"SQL: {result.get('sql_query')}",
    }

