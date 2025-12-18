import os

class Settings:

    DB_USER: str = os.getenv("ORACLE_USER", "system")
    DB_PASS: str = os.getenv("ORACLE_PASSWORD", "123456")
    
    DB_DSN: str = os.getenv("ORACLE_DSN", "oracle:1521/xe") 
    
    
    # LLM Modeli
    LLM_MODEL = os.getenv("LLM_MODEL", "tinyllama")
    
    # Mongo Ayarları
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:secretpassword@mongodb:27017")
    MONGO_DB_NAME = "ai_analytics_logs"


    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    

    TABLE_SCHEMA = """
    SALES (id, product_name, amount, sale_date)
    CUSTOMERS (id, name, city)
    """

settings = Settings()