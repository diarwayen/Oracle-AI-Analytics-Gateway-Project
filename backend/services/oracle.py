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
            
            # Yazma işlemleri için commit (Genelde SELECT kullanacağız ama dursun)
            if sql_query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")):
                self.connection.commit()
                return {"status": "success", "rows": cursor.rowcount}

            # Okuma işlemleri için sonuç döndür
            if cursor.description:
                columns = [col[0].upper() for col in cursor.description] # Kolon adlarını BÜYÜK harf yap
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return {"status": "success"}
        except oracledb.Error as e:
            logger.error(f"SQL Hatası: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()

    def get_schema_info(self) -> str:
        """
        MANUEL ŞEMA TANIMI:
        Sistem tablolarını sorgulamak yerine, projenin odaklandığı tabloyu
        ve kolonların işlevlerini doğrudan (hardcoded) veriyoruz.
        Bu yöntem LLM'in hata yapma riskini en aza indirir.
        """
        return """
TABLO ADI: IFSAPP.PERSONEL_ORG_AGACI_MV
AÇIKLAMA: Şirket personelinin organizasyonel, demografik ve iş durumunu içeren ana tablo.

ÖNEMLİ KOLONLAR VE ANLAMLARI:
- SIRKET (VARCHAR2): Şirket kodu.
- ISYERI_ADI (VARCHAR2): Çalışanın bağlı olduğu fabrika veya lokasyon adı (Örn: ANKARA FABRİKA).
- DEPARTMAN_ADI (VARCHAR2): Çalışanın departmanı (Örn: ÜRETİM, LOJİSTİK).
- CALISAN_ADI (VARCHAR2): Personelin Adı Soyadı.
- POZISYON_ACIKLAMASI (VARCHAR2): Çalışanın ünvanı / görevi.
- AKTIF_CALISAN (NUMBER): Çalışan şu an aktifse 1, değilse 0 değerini alır. 
  * "Toplam çalışan sayısı" sorulursa: SUM(AKTIF_CALISAN) kullanılmalıdır.
- ISE_BASLAYAN (NUMBER): Dönem içinde işe giren sayısı. Toplanabilir.
- ISTEN_AYRILAN (NUMBER): Dönem içinde işten ayrılan (turnover) sayısı. Toplanabilir.
- CINSIYET (VARCHAR2): Personel cinsiyeti.
- YAS (NUMBER): Personelin yaşı. (Ortalama yaş için AVG(YAS) kullanılabilir).
- EGITIM_SEVIYESI (VARCHAR2): Eğitim durumu (Lise, Lisans vb.).
- KIDEM_YILI (NUMBER): (Eğer varsa) Çalışma süresi.
- IKAMET_IL (VARCHAR2): Personelin yaşadığı şehir.
- MEDENI_DURUM (VARCHAR2): Evli/Bekar durumu.
"""

    def close(self) -> None:
        if self.connection:
            try:
                self.connection.close() # Havuza iade
                self.connection = None
            except: pass