import os

class Settings:
    # --- 1. ORACLE BAĞLANTI AYARLARI ---
    # services/oracle.py dosyasındaki isimlendirmeyle (ORACLE_...) birebir aynı olmalı
    ORACLE_USER = os.getenv("ORACLE_USER", "myuser")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "mypassword")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "oracle:1521/XEPDB1")
    ORACLE_LIB_DIR = os.getenv("ORACLE_LIB_DIR", "/opt/oracle/instantclient")

    # --- 2. GÜVENLİK AYARLARI ---
    # .env dosyası
    SECRET_KEY = os.getenv("SECRET_KEY", "gizli_anahtar_123")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    ORACLE_GATEWAY_API_KEY = os.getenv("ORACLE_GATEWAY_API_KEY", "gizli_anahtar_123")
    API_KEY_NAME = os.getenv("API_KEY_NAME", "X-API-Key")

    # --- 3. LLM VE AI AYARLARI ---
    LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

    # --- 4. MONGO AYARLARI ---
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:secretpassword@mongo:27017")
    MONGO_DB_NAME = "ai_analytics_logs"

    ALLOWED_TABLES  = ["PERSONEL_ORG_AGACI_MV"]
    # Eski schema stringi
    TABLE_SCHEMA = """
    SATISLAR (id, urun_id, adet, toplam_tutar, satis_tarihi, musteri_sehir)
    URUNLER (id, kategori, urun_adi, fiyat, stok_miktari)
    """

settings = Settings()