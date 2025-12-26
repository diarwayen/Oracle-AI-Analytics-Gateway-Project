from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Intern & Apprentice"])

# 1. KPI Kartları: Stajyer ve Çırak Sayıları
@router.get("/intern/kpi-summary")
@cache(expire=300)
async def get_intern_kpi(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SUM(CASE WHEN CTUR = 'Stajyer' THEN 1 ELSE 0 END) as "intern_count",
        SUM(CASE WHEN CTUR = 'Çırak' THEN 1 ELSE 0 END) as "apprentice_count",
        COUNT(CALISAN_ID) as "total_students"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTUR IN ('Stajyer', 'Çırak')
    """
    return oracle.execute_query(sql)

# 2. Detaylı Tablo: İşyeri, Departman vb. Kırılımlı Liste
@router.get("/intern/details-table")
@cache(expire=300)
async def get_intern_table(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        ISYERI_ADI as "location",
        DEPARTMAN_ADI as "department",
        CTUR as "type", -- Stajyer/Çırak
        CINSIYET as "gender",
        NVL(KAN_GRUBU, '-') as "blood_type",
        YAS_ARALIGI as "age_group",
        NVL(EGITIM_DURUMU, '-') as "education",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTUR IN ('Stajyer', 'Çırak')
    GROUP BY ISYERI_ADI, DEPARTMAN_ADI, CTUR, CINSIYET, KAN_GRUBU, YAS_ARALIGI, EGITIM_DURUMU
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)