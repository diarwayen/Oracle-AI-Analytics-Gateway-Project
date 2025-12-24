import oracledb
import logging
from typing import Dict, Any, Optional, List

from core.config import settings
from services.db.base import QueryExecutor, SchemaProvider

logger = logging.getLogger(__name__)

# Global Bağlantı Havuzu
_pool = None

def init_pool():
    global _pool
    if _pool is None:
        try:
            logger.info("Oracle Connection Pool oluşturuluyor...")
            _pool = oracledb.create_pool(
                user=settings.ORACLE_USER,
                password=settings.ORACLE_PASSWORD,
                dsn=settings.ORACLE_DSN,
                min=2, max=10, increment=1
            )
            logger.info("Oracle Connection Pool başarıyla oluşturuldu.")
        except Exception as e:
            logger.error(f"Pool oluşturma hatası: {e}")
            raise e

def close_pool():
    global _pool
    if _pool:
        try:
            _pool.close()
            _pool = None
            logger.info("Oracle Connection Pool kapatıldı.")
        except Exception as e:
            logger.error(f"Pool kapatma hatası: {e}")

class OracleService(QueryExecutor, SchemaProvider):
    def __init__(self):
        self.connection = None

    def connect(self) -> None:
        global _pool
        if _pool is None:
            init_pool()
        try:
            self.connection = _pool.acquire()
        except Exception as e:
            logger.error(f"Pool hatası: {e}")
            raise e

    def execute_query(self, sql_query: str, params: Optional[Dict[str, Any]] = None):
        if not self.connection:
            raise Exception("Bağlantı yok!")
        cursor = self.connection.cursor()
        try:
            if params is None: params = {}
            cursor.execute(sql_query, params)
            
            if sql_query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")):
                self.connection.commit()
                return {"status": "success", "rows": cursor.rowcount}

            if cursor.description:
                columns = [col[0].lower() for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return {"status": "success"}
        except oracledb.Error as e:
            logger.error(f"SQL Hatası: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()

    def get_schema_info(self) -> str:
        """
        DİNAMİK ŞEMA ANALİZİ (FİLTRELİ):
        Sadece config.py içindeki ALLOWED_TABLES listesindeki tabloları çeker.
        """
        
        # Filtre Listesini Hazırla
        allowed_list = settings.ALLOWED_TABLES
        
        # Eğer liste boşsa güvenlik için hata döndürebilir veya hepsi çekilebilir.
        # Bizim senaryoda boşsa "Hiçbir şey çekme" veya "Hepsini çek" kararı verilmeli.
        # Güvenli olan: Liste doluysa filtrele.
        
        filter_sql = ""
        if allowed_list and len(allowed_list) > 0:
            # SQL Injection'a karşı basit önlem: Sadece harf/sayı/altçizgi
            # Ama config dosyasından geldiği için güveniyoruz.
            table_names_str = "', '".join([t.upper().strip() for t in allowed_list])
            filter_sql = f"AND table_name IN ('{table_names_str}')"
        
        # 1. Tabloları ve Kolonları Çek (Filtreli)
        cols_sql = f"""
            SELECT table_name, column_name, data_type
            FROM user_tab_columns
            WHERE 1=1
            {filter_sql}
            ORDER BY table_name, column_id
        """
        
        # 2. İlişkileri Çek (Filtreli)
        # Sadece ilgili tabloların ilişkilerini getir
        relations_sql = f"""
            SELECT 
                a.table_name, 
                a.column_name, 
                c_pk.table_name as r_table_name, 
                c_pk.constraint_type
            FROM user_cons_columns a
            JOIN user_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
            LEFT JOIN user_constraints c_pk ON c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name
            WHERE c.constraint_type IN ('P', 'R')
            {filter_sql} 
        """

        try:
            columns = self.execute_query(cols_sql)
            relations = self.execute_query(relations_sql)
            
            if isinstance(columns, dict) and "error" in columns:
                return f"Şema hatası: {columns['error']}"

            if not columns:
                return "HATA: İzin verilen tablolar veritabanında bulunamadı veya yetki yok."

            # İlişkileri haritala
            rel_map = {}
            if isinstance(relations, list):
                for r in relations:
                    key = f"{r['TABLE_NAME']}.{r['COLUMN_NAME']}"
                    if r['CONSTRAINT_TYPE'] == 'P':
                        rel_map[key] = "(Primary Key)"
                    elif r['CONSTRAINT_TYPE'] == 'R' and r['R_TABLE_NAME']:
                        rel_map[key] = f"(Foreign Key -> {r['R_TABLE_NAME']} tablosuna bağlanır)"

            # Metni Oluştur
            schema_text = "FİLTRELENMİŞ VERİTABANI ŞEMASI:\n"
            current_table = ""

            for row in columns:
                t = row['TABLE_NAME']
                c = row['COLUMN_NAME']
                d = row['DATA_TYPE']
                
                if t != current_table:
                    schema_text += f"\n---------------------------------\nTABLO: {t}\n"
                    current_table = t
                
                extra_info = rel_map.get(f"{t}.{c}", "")
                schema_text += f"  - {c} ({d}) {extra_info}\n"

            return schema_text

        except Exception as e:
            return f"Şema bilgisi alınamadı: {str(e)}"

    def close(self) -> None:
        if self.connection:
            try:
                self.connection.close() # Havuza iade
                self.connection = None
            except: pass