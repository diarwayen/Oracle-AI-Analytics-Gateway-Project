from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Turnover"])

# 1. Aylara Göre Hareket Grafiği (İşe Giriş / Çıkış / Bölüm Değişikliği)
# Bu endpoint Metrik 1, 2, 3, 4 ve 6'yı TEK SEFERDE getirir.
@router.get("/turnover/timeline")
@cache(expire=300)
async def get_turnover_timeline(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        YILAY as "year_month",
        SUM(CASE WHEN ISE_BASLAYAN = 1 THEN 1 ELSE 0 END) as "hires",
        SUM(CASE WHEN ISTEN_AYRILAN = 1 THEN 1 ELSE 0 END) as "leavers",
        SUM(CASE WHEN BOLUMDEN_AYRILAN = 1 AND ISTEN_AYRILAN = 0 THEN 1 ELSE 0 END) as "transfers"
    FROM IFSAPP.PERSONEL_ORG_AGACI_AYYIL_MV
    WHERE DIREKTORLUK_REF = '1'
    GROUP BY YILAY
    ORDER BY YILAY ASC
    """
    return oracle.execute_query(sql)

# 2. Detaylı Hareket Tablosu (Metrik 5)
@router.get("/turnover/details")
@cache(expire=300)
async def get_turnover_details(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        YILAY as "period",
        SIRKET as "company",
        ISYERI_ADI as "location",
        CALISAN_ADI as "name",
        CASE 
            WHEN ISE_BASLAYAN = 1 THEN 'İşe Giriş'
            WHEN ISTEN_AYRILAN = 1 THEN 'İşten Çıkış'
            ELSE 'Diğer'
        END as "movement_type",
        POZISYON as "position",
        EGITIM_DURUMU as "education"
    FROM IFSAPP.PERSONEL_ORG_AGACI_AYYIL_MV
    WHERE DIREKTORLUK_REF = '1' 
      AND (ISE_BASLAYAN = 1 OR ISTEN_AYRILAN = 1)
    ORDER BY YILAY DESC, SIRKET
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)


