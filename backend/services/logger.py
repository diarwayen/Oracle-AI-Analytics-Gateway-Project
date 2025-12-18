import datetime
from pymongo import MongoClient
from core.config import settings

class AuditLogger:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):

        try:
  
            self.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client[settings.MONGO_DB_NAME]
            self.collection = self.db["interactions"] # Tablo adı 'interactions' olsun

            self.client.server_info()
            print("MongoDB Loglama Servisi Bağlandı.")
        except Exception as e:
            print(f"MongoDB'ye bağlanılamadı. Loglama devre dışı. Hata: {e}")
            self.client = None

    def log_interaction(self, user_question, sql_generated, success, error_message=None, row_count=0):

        
        # Eğer bağlantı yoksa loglama yapma, uygulamayı da kırma.
        if not self.client:
            return

        log_entry = {
            "timestamp": datetime.datetime.utcnow(),
            "question": user_question,
            "generated_sql": sql_generated,
            "success": success,
            "row_count": row_count,  # Kaç satır veri döndü?
            "error_details": str(error_message) if error_message else None,
            "app_version": "1.0.0"
        }

        try:
            self.collection.insert_one(log_entry)
        except Exception as e:
            print(f"Log yazarken hata oluştu: {e}")

# Tek bir instance oluşturup dışarı açıyoruz (Singleton mantığı)
logger = AuditLogger()