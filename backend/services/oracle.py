import oracledb
import logging
from typing import Dict, Any, Optional, List

from core.config import settings
from services.db.base import QueryExecutor, SchemaProvider

logger = logging.getLogger(__name__)

# Global Bağlantı Havuzu Değişkeni
_pool = None

def init_pool():
    """
    Uygulama başlarken (main.py lifespan içinde) çağrılır.
    Veritabanı bağlantı havuzunu oluşturur.
    """
    global _pool
    if _pool is None:
        try:
            logger.info("Oracle Connection Pool oluşturuluyor...")
            _pool = oracledb.create_pool(
                user=settings.ORACLE_USER,
                password=settings.ORACLE_PASSWORD,
                dsn=settings.ORACLE_DSN,
                min=2,      # En az 2 bağlantı hep açık kalsın
                max=10,     # Trafik artarsa en fazla 10'a çıksın
                increment=1 # İhtiyaç oldukça 1'er 1'er artır
            )
            logger.info("Oracle Connection Pool başarıyla oluşturuldu.")
        except Exception as e:
            logger.error(f"Pool oluşturma hatası: {e}")
            raise e

def close_pool():
    """Uygulama kapanırken çağrılır ve havuzu temizler."""
    global _pool
    if _pool:
        try:
            _pool.close()
            _pool = None
            logger.info("Oracle Connection Pool kapatıldı.")
        except Exception as e:
            logger.error(f"Pool kapatma hatası: {e}")

class OracleService(QueryExecutor, SchemaProvider):
    """
    OracleService artık bağlantıları Pool'dan ödünç alıyor.
    QueryExecutor ve SchemaProvider arayüzlerine sadık kalır.
    """

    def __init__(self):
        self.connection = None

    def connect(self) -> None:
        """Havuzdan bir bağlantı ödünç alır (Acquire)."""
        global _pool
        if _pool is None:
            # Geliştirme ortamında veya script çalıştırırken pool init edilmemiş olabilir
            logger.warning("Pool bulunamadı, init_pool() çağrılıyor...")
            init_pool()
        
        try:
            self.connection = _pool.acquire()
        except Exception as e:
            logger.error(f"Pool'dan bağlantı alma hatası: {e}")
            raise e

    def execute_query(self, sql_query: str, params: Optional[Dict[str, Any]] = None):
        if not self.connection:
            raise Exception("Veritabanı bağlantısı yok! Önce connect() çağırın.")

        cursor = self.connection.cursor()
        try:
            if params is None:
                params = {}

            cursor.execute(sql_query, params)

            # DML (Insert/Update/Delete) işlemleri için Commit gerekir
            if sql_query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")):
                self.connection.commit()
                return {"status": "success", "rows_affected": cursor.rowcount if cursor.rowcount != -1 else "Done"}

            # SELECT işlemleri için
            if cursor.description:
                columns = [col[0].lower() for col in cursor.description]
                rows = cursor.fetchall()
                result: List[Dict[str, Any]] = []
                for row in rows:
                    result.append(dict(zip(columns, row)))
                return result
            else:
                return {"status": "success", "info": "No rows returned"}

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

            if isinstance(rows, list) is False and "error" in rows:
                return f"Şema hatası: {rows['error']}"

            schema_text = "Veritabanı Şeması:\n"
            current_table = ""

            # execute_query artık liste döndürdüğü için iterasyon güvenli
            for row in rows:
                if not isinstance(row, dict): continue # Güvenlik kontrolü
                
                table = row.get("table_name")
                col = row.get("column_name")
                dtype = row.get("data_type")

                if table != current_table:
                    schema_text += f"\nTablo: {table}\nKolonlar: "
                    current_table = table

                schema_text += f"{col} ({dtype}), "

            return schema_text

        except Exception as e:
            return f"Şema bilgisi alınamadı: {str(e)}"

    def close(self) -> None:
        """Bağlantıyı havuza geri iade eder (Release)."""
        if self.connection:
            try:
                # Pool modunda .close(), bağlantıyı kapatmaz, havuza geri bırakır.
                self.connection.close()
                self.connection = None
            except Exception as e:
                logger.error(f"Bağlantı iade hatası: {e}")