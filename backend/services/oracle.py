import oracledb
from core.config import settings

def run_query(sql_query: str):
    """Oracle'da SQL çalıştırır"""
    
    # Güvenlik Kontrolü
    forbidden = ["DELETE", "DROP", "TRUNCATE", "INSERT", "UPDATE", "ALTER"]
    if any(word in sql_query.upper() for word in forbidden):
        return {"error": "Güvenlik Uyarısı: Sadece okuma yapılabilir!"}

    connection = None
    cursor = None
    try:
        connection = oracledb.connect(
            user=settings.DB_USER, 
            password=settings.DB_PASS, 
            dsn=settings.DB_DSN
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)
        
        # Sonucu Dictionary olarak al
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))
            return cursor.fetchall()
        return []
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if cursor: cursor.close()
        if connection: connection.close()