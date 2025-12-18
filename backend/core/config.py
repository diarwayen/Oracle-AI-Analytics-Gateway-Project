import os

class Settings:
    # --- Veritabanı Bilgileri ---
    # Not: Docker içinde "localhost" çalışmaz. Servis adını (örn: oracle) kullanmalısın.
    # Eğer docker-compose.yml içinde servisin adı "oracle" ise:
    DB_USER: str = os.getenv("ORACLE_USER", "system")
    DB_PASS: str = os.getenv("ORACLE_PASSWORD", "123456") # Şifreni buraya yaz veya env'den al
    
    # "localhost" yerine "oracle" yazıyoruz (Servis adı)
    DB_DSN: str = os.getenv("ORACLE_DSN", "oracle:1521/xe") 
    
    # --- AI ve Loglama Ayarları ---
    
    # LLM Modeli
    LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
    
    # Mongo Ayarları
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:secretpassword@mongodb:27017")
    MONGO_DB_NAME = "ai_analytics_logs"

    # Ollama Adresi (Docker içinden erişim için servis adı kullanılır)
    # Burası SINIFIN İÇİNDE olmalı (Girintiye dikkat)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    
    # --- Tablo Yapısı (AI İçin Bilgi) ---
    TABLE_SCHEMA = """
    SALES (id, product_name, amount, sale_date)
    CUSTOMERS (id, name, city)
    """

# Ayarları dışarı aç
settings = Settings()