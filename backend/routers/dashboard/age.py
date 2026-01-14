from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

# Endpoint prefix ve tag'i
router = APIRouter(tags=["Age"])

# ----------------------------------------------------------------
# 1. KPI KARTLARI
# ----------------------------------------------------------------

@router.get("/age/kpi-summary")
@cache(expire=300)
async def get_age_kpi_summary(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        -- 1. Ortalama Yaş
        ROUND(AVG(YAS), 1) as "avg_age",
        
        -- 2. 15-18 Yaş
        SUM(CASE WHEN YAS_ARALIGI = '15-18' THEN 1 ELSE 0 END) as "age_15_18",
        
        -- 3. 19-29 Yaş
        SUM(CASE WHEN YAS_ARALIGI = '19-29' THEN 1 ELSE 0 END) as "age_19_29",
        
        -- 4. 30-39 Yaş
        SUM(CASE WHEN YAS_ARALIGI = '30-39' THEN 1 ELSE 0 END) as "age_30_39",
        
        -- 5. 40-49 Yaş
        SUM(CASE WHEN YAS_ARALIGI = '40-49' THEN 1 ELSE 0 END) as "age_40_49",
        
        -- 6. 50+ Yaş
        SUM(CASE WHEN YAS_ARALIGI = '50+' THEN 1 ELSE 0 END) as "age_50_plus"

    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1'
      -- CTURS filtresi bazı sorgularda vardı, genele ekliyoruz:
      AND CTURS = 1
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 2. GRAFİKLER (PIE & HEATMAP)
# ----------------------------------------------------------------

# Metrik 9: Genel Yaş Dağılımı (Pie Chart)
@router.get("/age/distribution")
@cache(expire=300)
async def get_age_distribution(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(YAS_ARALIGI, 'Bilinmiyor') as "age_group", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
    GROUP BY YAS_ARALIGI 
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# Metrik 8: Şirket Bazlı Yaş Heatmap
@router.get("/age/company-heatmap")
@cache(expire=300)
async def get_company_age_heatmap(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", 
        NVL(YAS_ARALIGI, 'Diğer') as "age_group", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
    GROUP BY SIRKET, YAS_ARALIGI 
    ORDER BY SIRKET ASC, YAS_ARALIGI ASC
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 3. DETAYLI TABLOLAR
# ----------------------------------------------------------------

# Metrik 7: Yönetime Bağlı Birimler (Departman & Lokasyon)
@router.get("/age/department-location")
@cache(expire=300)
async def get_table_dept_location(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        ISYERI_ADI as "location",
        DEPARTMAN_ADI as "department",
        NVL(YAS_ARALIGI, 'Bilinmiyor') as "age_group",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY ISYERI_ADI, DEPARTMAN_ADI, YAS_ARALIGI
    ORDER BY ISYERI_ADI, DEPARTMAN_ADI, YAS_ARALIGI DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 10: İşyeri ve Cinsiyet Bazlı
@router.get("/age/location-gender")
@cache(expire=300)
async def get_table_location_gender(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        ISYERI_ADI as "location",
        CINSIYET as "gender",
        NVL(YAS_ARALIGI, 'Bilinmiyor') as "age_group",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY ISYERI_ADI, CINSIYET, YAS_ARALIGI
    ORDER BY ISYERI_ADI, YAS_ARALIGI ASC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 11: Pozisyon ve Cinsiyet Bazlı
@router.get("/age/position-gender")
@cache(expire=300)
async def get_table_position_gender(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(POZISYON, 'POZİSYON BİLGİSİ BOŞ') as "position",
        NVL(YAS_ARALIGI, 'Bilinmiyor') as "age_group",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY NVL(POZISYON, 'POZİSYON BİLGİSİ BOŞ'), YAS_ARALIGI, CINSIYET
    ORDER BY POZISYON, YAS_ARALIGI DESC
    FETCH FIRST 100000 ROWS ONLY
    """
    return oracle.execute_query(sql)