from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Blood"])

# 1. KPI KARTLARI (Tüm Kan Grupları Tek Sorguda)
@router.get("/blood/kpi-summary")
@cache(expire=300)
async def get_blood_kpi(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        COUNT(CALISAN_ID) as "total",
        SUM(CASE WHEN KAN_GRUBU = 'A+' THEN 1 ELSE 0 END) as "a_pos",
        SUM(CASE WHEN KAN_GRUBU = 'A-' THEN 1 ELSE 0 END) as "a_neg",
        SUM(CASE WHEN KAN_GRUBU = 'B+' THEN 1 ELSE 0 END) as "b_pos",
        SUM(CASE WHEN KAN_GRUBU = 'B-' THEN 1 ELSE 0 END) as "b_neg",
        SUM(CASE WHEN KAN_GRUBU = 'AB+' THEN 1 ELSE 0 END) as "ab_pos",
        SUM(CASE WHEN KAN_GRUBU = 'AB-' THEN 1 ELSE 0 END) as "ab_neg",
        SUM(CASE WHEN KAN_GRUBU = 'O+' THEN 1 ELSE 0 END) as "o_pos",
        SUM(CASE WHEN KAN_GRUBU = 'O-' THEN 1 ELSE 0 END) as "o_neg"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    """
    return oracle.execute_query(sql)

# 2. Kan Grubu Dağılımı (Pie Chart)
@router.get("/blood/distribution")
@cache(expire=300)
async def get_blood_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(KAN_GRUBU, 'Bilinmiyor') as "blood_type", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
    GROUP BY KAN_GRUBU 
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# 3. Detaylı Tablo (İşyeri & Cinsiyet & Kan Grubu)
@router.get("/blood/table-details")
@cache(expire=300)
async def get_blood_table(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company",
        ISYERI_ADI as "location",
        NVL(KAN_GRUBU, 'Bilinmiyor') as "blood_type",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY SIRKET, ISYERI_ADI, KAN_GRUBU, CINSIYET
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)





