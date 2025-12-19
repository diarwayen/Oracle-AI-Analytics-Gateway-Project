import oracledb
import os
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class OracleService:
    def __init__(self):
        self.user = settings.ORACLE_USER
        self.password = settings.ORACLE_PASSWORD
        self.dsn = settings.ORACLE_DSN
        self.connection = None

    def connect(self):
        try:
            # Thin mode varsayılan olarak aktiftir, lib_dir belirtmeye gerek yok
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            # logger.info("Oracle bağlantısı başarılı.") # Log kirliliği yapmaması için kapattım
        except Exception as e:
            logger.error(f"Oracle bağlantı hatası: {e}")
            raise e

    # --- DÜZELTME BURADA YAPILDI ---
    def execute_query(self, sql_query: str, params: dict = None):
        """
        SQL sorgusunu çalıştırır ve sonuçları Dictionary listesi olarak döner.
        params: SQL bind değişkenleri (Opsiyonel)
        """
        if not self.connection:
            raise Exception("Veritabanı bağlantısı yok!")
        
        cursor = self.connection.cursor()
        try:
            # Eğer params gelmediyse boş sözlük ata
            if params is None:
                params = {}
            
            cursor.execute(sql_query, params)
            
            # Eğer SELECT sorgusu değilse (INSERT, UPDATE vb.) commit et ve çık
            if sql_query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.connection.commit()
                return {"status": "success", "rows_affected": cursor.rowcount}

            # Sütun isimlerini al
            columns = [col[0].lower() for col in cursor.description]
            
            # Verileri çek ve Dict formatına çevir
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
                
            return result
            
        except oracledb.Error as e:
            error_obj, = e.args
            logger.error(f"SQL Hatası: {error_obj.message}")
            return {"error": error_obj.message}
        finally:
            cursor.close()

    def get_schema_info(self):
        """
        AI için veritabanı şemasını özetler.
        """
        schema_query = """
        SELECT table_name, column_name, data_type 
        FROM user_tab_columns 
        ORDER BY table_name, column_id
        """
        try:
            # Buradaki çağrı params olmadığı için eski haliyle de çalışıyordu,
            # ama execute_query güncellenince burası da sorunsuz çalışır.
            rows = self.execute_query(schema_query)
            
            if isinstance(rows, dict) and "error" in rows:
                return f"Şema hatası: {rows['error']}"

            schema_text = "Veritabanı Şeması:\n"
            current_table = ""
            
            for row in rows:
                table = row['table_name']
                col = row['column_name']
                dtype = row['data_type']
                
                if table != current_table:
                    schema_text += f"\nTablo: {table}\nKolonlar: "
                    current_table = table
                
                schema_text += f"{col} ({dtype}), "
                
            return schema_text
            
        except Exception as e:
            return f"Şema bilgisi alınamadı: {str(e)}"

    def close(self):
        if self.connection:
            try:
                self.connection.close()
                # logger.info("Oracle bağlantısı kapatıldı.")
            except Exception as e:
                logger.error(f"Bağlantı kapatma hatası: {e}")