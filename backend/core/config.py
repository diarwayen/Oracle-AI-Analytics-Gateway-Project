import os

class Settings:

    # Veritabanı Bilgileri
    DB_USER = os.getenv("ORACLE_USER")
    DB_PASS = os.getenv("ORACLE_PASSWORD")
    DB_DSN = os.getenv("ORACLE_DSN")
    
    # Örn: http://ollama:11434
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:secretpassword@mongodb:27017")
    MONGO_DB_NAME = "ai_analytics_logs"

    # Tablo Yapısı (Sabit)
    TABLE_SCHEMA = """
    SALES (id, product_name, amount, sale_date)
    CUSTOMERS (id, name, city)
    """

# Ayarları dışarı aç
settings = Settings()