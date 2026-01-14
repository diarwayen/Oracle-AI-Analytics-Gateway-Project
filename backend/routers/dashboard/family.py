from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Family & Marital Status"])

# 1. KPI Kartları: Genel Sayılar (Çocuklu, Çocuksuz vb.)
@router.get("/family/kpi-summary")
@cache(expire=300)
async def get_family_kpi(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        COUNT(CALISAN_ID) as "total_employees",
        SUM(CASE WHEN COCUK_DURUMU = '1' THEN 1 ELSE 0 END) as "has_children",
        SUM(CASE WHEN COCUK_DURUMU = '0' THEN 1 ELSE 0 END) as "no_children"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    """
    return oracle.execute_query(sql)

# 2. Grafik: Medeni Durum Dağılımı (Sadece Bilinenler)
# İsteğine uygun olarak sayı yerine Chart verisi hazırlıyoruz.
@router.get("/family/distribution/marital-status")
@cache(expire=300)
async def get_marital_distribution(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        MEDENI_DURUM as "status",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
      AND MEDENI_DURUM IN ('EVLİ', 'BEKAR') -- Sadece bu ikisi istendi
    GROUP BY MEDENI_DURUM
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# 3. Grafik: Cinsiyete Göre Medeni Durum
@router.get("/family/distribution/gender-marital")
@cache(expire=300)
async def get_gender_marital_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        CINSIYET as "gender",
        MEDENI_DURUM as "status",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
      AND MEDENI_DURUM IN ('EVLİ', 'BEKAR')
    GROUP BY CINSIYET, MEDENI_DURUM
    ORDER BY CINSIYET, "count" DESC
    """
    return oracle.execute_query(sql)

# 4. Grafik: Cinsiyete Göre Çocuk Durumu
@router.get("/family/distribution/gender-children")
@cache(expire=300)
async def get_gender_children_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        CINSIYET as "gender", 
        CASE 
            WHEN COCUK_DURUMU = '1' THEN 'Çocuk Var'
            WHEN COCUK_DURUMU = '0' THEN 'Çocuk Yok'
            ELSE 'Bilinmiyor'
        END AS "child_status", 
        COUNT(CALISAN_ID) AS "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
    GROUP BY CINSIYET, 
        CASE 
            WHEN COCUK_DURUMU = '1' THEN 'Çocuk Var'
            WHEN COCUK_DURUMU = '0' THEN 'Çocuk Yok'
            ELSE 'Bilinmiyor'
        END 
    ORDER BY COUNT(CALISAN_ID) DESC
    """
    return oracle.execute_query(sql)




