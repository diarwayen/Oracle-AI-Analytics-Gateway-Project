from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import oracledb
import requests
import json
import os

app = FastAPI()


DB_USER = os.getenv("ORACLE_USER")
DB_PASS = os.getenv("ORACLE_PASSWORD")
DB_DSN =  os.getenv("ORACLE_DSN")

if not DB_USER or not DB_PASSWORD:
    raise RuntimeError("....")


class QueryRequest(BaseModel):
    user_question: str

def run_oracle_query(sql_query):
    """Oracle'da SQL çalıştırıp sonucu JSON (dict) listesi döner"""
    try:
            connection = oracledb.connect(
            user=DB_USER, 
            password=DB_PASSWORD, 
            dsn=DB_DSN )
        
        # Sütun isimlerini al
        columns = [col[0] for col in cursor.description]
        cursor.rowfactory = lambda *args: dict(zip(columns, args))
        
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        return data
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"status": "Gateway Calisiyor"}

# SENARYO 1: Sabit Veri (Grafana sadece bu URL'i çağırır)
@app.get("/api/top-sales")
def get_top_sales():
    sql = "SELECT product_name, amount FROM sales ORDER BY amount DESC FETCH FIRST 10 ROWS ONLY"
    return run_oracle_query(sql)

# SENARYO 2: LLM ile Dinamik Sorgu
@app.post("/api/ask-ai")
def ask_ai(request: QueryRequest):
    # 1. Ollama'ya (Mistral) Prompt Gönder
    prompt = f"""
    Sen bir SQL uzmanısın. Oracle Database kullanıyoruz.
    Tablo şeması: SALES (id, product_name, amount, sale_date), CUSTOMERS (id, name, city).
    
    Kullanıcı sorusu: {request.user_question}
    
    Sadece ve sadece SQL sorgusunu yaz. Başka hiçbir açıklama yapma.
    """
    
    ollama_response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )
    
    generated_sql = ollama_response.json().get("response").strip()
    
    # Güvenlik önlemi: DELETE/DROP gibi komutları engellemek gerekebilir!
    
    # 2. Üretilen SQL'i Oracle'da çalıştır
    result = run_oracle_query(generated_sql)
    
    return {
        "generated_sql": generated_sql,
        "data": result
    }