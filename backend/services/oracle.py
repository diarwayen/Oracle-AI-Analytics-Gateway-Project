import oracledb
import logging
from typing import Dict, Any, Optional, List

from core.config import settings
from services.db.base import QueryExecutor, SchemaProvider

logger = logging.getLogger(__name__)


class OracleService(QueryExecutor, SchemaProvider):
    """
    Oracle adapter: QueryExecutor + SchemaProvider arayüzlerini uygular.
    Bu sınıf Oracle'a özel; farklı tablo yapılarına uyum için kod değişmeden
    çalışır, çünkü şema bilgisi dinamik çekilir.
    """

    def __init__(self):
        self.user = settings.ORACLE_USER
        self.password = settings.ORACLE_PASSWORD
        self.dsn = settings.ORACLE_DSN
        self.connection = None

    def connect(self) -> None:
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
            )
        except Exception as e:
            logger.error(f"Oracle bağlantı hatası: {e}")
            raise e

    def execute_query(self, sql_query: str, params: Optional[Dict[str, Any]] = None):
        if not self.connection:
            raise Exception("Veritabanı bağlantısı yok!")

        cursor = self.connection.cursor()
        try:
            if params is None:
                params = {}

            cursor.execute(sql_query, params)

            if sql_query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.connection.commit()
                return {"status": "success", "rows_affected": cursor.rowcount}

            columns = [col[0].lower() for col in cursor.description]
            rows = cursor.fetchall()
            result: List[Dict[str, Any]] = []
            for row in rows:
                result.append(dict(zip(columns, row)))

            return result

        except oracledb.Error as e:
            error_obj, = e.args
            logger.error(f"SQL Hatası: {error_obj.message}")
            return {"error": error_obj.message}
        finally:
            cursor.close()

    def get_schema_info(self) -> str:
        schema_query = """
        SELECT table_name, column_name, data_type 
        FROM user_tab_columns 
        ORDER BY table_name, column_id
        """
        try:
            rows = self.execute_query(schema_query)

            if isinstance(rows, dict) and "error" in rows:
                return f"Şema hatası: {rows['error']}"

            schema_text = "Veritabanı Şeması:\n"
            current_table = ""

            for row in rows:
                table = row["table_name"]
                col = row["column_name"]
                dtype = row["data_type"]

                if table != current_table:
                    schema_text += f"\nTablo: {table}\nKolonlar: "
                    current_table = table

                schema_text += f"{col} ({dtype}), "

            return schema_text

        except Exception as e:
            return f"Şema bilgisi alınamadı: {str(e)}"

    def close(self) -> None:
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logger.error(f"Bağlantı kapatma hatası: {e}")