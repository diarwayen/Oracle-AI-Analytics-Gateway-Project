from typing import Generator

from services.oracle import OracleService
from services.db.base import QueryExecutor, SchemaProvider


def get_oracle_service() -> Generator[OracleService, None, None]:
    svc = OracleService()
    try:
        svc.connect()
        yield svc
    finally:
        svc.close()


def get_executor_factory():
    # Varsayılan olarak Oracle executor döndürür; ileride kolayca değiştirilebilir.
    return OracleService


# Tip ipucu için (Oracle hem executor hem schema provider)
OracleExecutor = OracleService
OracleSchemaProvider = OracleService

