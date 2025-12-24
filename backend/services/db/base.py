from typing import Protocol, Any, Dict, List, Optional


class QueryExecutor(Protocol):
    """Minimal DB executor interface for OCP."""

    def connect(self) -> None: ...
    def execute_query(self, sql_query: str, params: Optional[Dict[str, Any]] = None) -> Any: ...
    def close(self) -> None: ...


class SchemaProvider(Protocol):
    """Exposes database schema summary for LLM prompts."""

    def get_schema_info(self) -> str: ...

