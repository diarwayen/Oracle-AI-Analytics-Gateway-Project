import oracledb
import logging
from core.config import settings

# Loglama
logger = logging.getLogger(__name__)

class OracleService:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """Veritabanına bağlanır"""
        try:
            # Senin eski kodundaki ayarları kullanıyoruz (DB_USER, DB_DSN vs.)
            # Eğer config.py'de isimler farklıysa (ORACLE_USER gibi) burayı düzeltmen gerekir.
            self.connection = oracledb.connect(
                user=settings.DB_USER,
                password=settings.DB_PASS,
                dsn=settings.DB_DSN
            )
            self.cursor = self.connection.cursor()
            logger.info("Oracle bağlantısı başarılı (Thin Mode).")
        except Exception as e:
            logger.error(f"Oracle bağlantı hatası: {str(e)}")
            raise e

    def get_schema_info(self):
        """
        AI'ya 'Bak benim tablolarım bunlar' diyebilmek için şema bilgisini çeker.
        Bu fonksiyon eskiden sende yoktu, yeni ekledik.
        """
        try:
            if not self.cursor:
                self.connect()

            # Kullanıcının tablolarını ve kolonlarını çek
            query = """
                SELECT table_name, column_name, data_type 
                FROM user_tab_columns 
                ORDER BY table_name, column_id
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            # AI için okunabilir metne çevir
            schema_text = "Veritabanı Şeması:\n"
            current_table = ""
            
            for row in rows:
                # oracledb tuple döner: (TABLE_NAME, COLUMN_NAME, DATA_TYPE)
                t_name, c_name, d_type = row[0], row[1], row[2]
                
                if t_name != current_table:
                    schema_text += f"\nTablo: {t_name}\nKolonlar: "
                    current_table = t_name
                
                schema_text += f"{c_name} ({d_type}), "
            
            return schema_text

        except Exception as e:
            logger.error(f"Şema çekilemedi: {str(e)}")
            return "Şema bilgisi alınamadı (Hata oluştu)."

    def execute_query(self, sql_query: str):
        """
        AI'dan gelen SQL'i çalıştırır.
        """
        # Güvenlik Kontrolü (Senin eski kodundan aldım)
        forbidden = ["DELETE", "DROP", "TRUNCATE", "INSERT", "UPDATE", "ALTER"]
        if any(word in sql_query.upper() for word in forbidden):
            return {"error": "Güvenlik Uyarısı: Sadece okuma (SELECT) yapılabilir!"}

        try:
            if not self.cursor:
                self.connect()

            # Noktalı virgül temizliği (Oracle sevmez)
            sql_query = sql_query.replace(";", "")
            
            self.cursor.execute(sql_query)
            
            # Sonucu Dictionary Listesi olarak al
            if self.cursor.description:
                columns = [col[0] for col in self.cursor.description]
                self.cursor.rowfactory = lambda *args: dict(zip(columns, args))
                return self.cursor.fetchall()
            
            return []

        except Exception as e:
            logger.error(f"SQL Hatası: {str(e)}")
            return {"error": str(e)}

    def close(self):
        """Bağlantıyı kapatır"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception:
            pass