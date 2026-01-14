from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Engagement"])

# 1. KPI Kartları: Ortalama Süreler
@router.get("/engagement/kpi-summary")
@cache(expire=300)
async def get_engagement_kpi(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        -- Ortalama Çalışma Süresi (Yıl/Ay cinsinden olabilir)
        NVL(AVG(CALISMA_SURESI), 0) as "avg_work_duration",
        
        -- Ortalama Ayrılma Süresi
        NVL(AVG(AYRILMA_SURESI), 0) as "avg_leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    """
    return oracle.execute_query(sql)

# 2. Grafik: İşyerlerine Göre Bağlılık
@router.get("/engagement/by-location")
@cache(expire=300)
async def get_engagement_by_location(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        ISYERI_ADI as "location",
        NVL(AVG(CALISMA_SURESI), 0) as "avg_work_duration",
        NVL(AVG(AYRILMA_SURESI), 0) as "avg_leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    GROUP BY ISYERI_ADI
    ORDER BY "avg_work_duration" DESC
    FETCH FIRST 100 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 3. Grafik: Departmanlara Göre Bağlılık
@router.get("/engagement/by-department")
@cache(expire=300)
async def get_engagement_by_department(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        DEPARTMAN_ADI as "department",
        NVL(AVG(CALISMA_SURESI), 0) as "avg_work_duration",
        NVL(AVG(AYRILMA_SURESI), 0) as "avg_leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    GROUP BY DEPARTMAN_ADI
    ORDER BY "avg_work_duration" DESC
    FETCH FIRST 100 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 4. Grafik: Medeni Duruma Göre
@router.get("/engagement/by-marital")
@cache(expire=300)
async def get_engagement_by_marital(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        MEDENI_DURUM as "status",
        NVL(AVG(CALISMA_SURESI), 0) as "avg_work_duration",
        NVL(AVG(AYRILMA_SURESI), 0) as "avg_leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    GROUP BY MEDENI_DURUM
    ORDER BY "avg_work_duration" DESC
    """
    return oracle.execute_query(sql)

# 5. Grafik: Yaş Aralıklarına Göre
@router.get("/engagement/by-age-group")
@cache(expire=300)
async def get_engagement_by_age(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        YAS_ARALIGI as "age_group",
        NVL(AVG(CALISMA_SURESI), 0) as "avg_work_duration",
        NVL(AVG(AYRILMA_SURESI), 0) as "avg_leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    GROUP BY YAS_ARALIGI
    ORDER BY "avg_work_duration" DESC
    """
    return oracle.execute_query(sql)

# 6. Grafik: Eğitim Durumuna Göre
@router.get("/engagement/by-education")
@cache(expire=300)
async def get_engagement_by_education(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        EGITIM_DURUMU as "education",
        NVL(AVG(CALISMA_SURESI), 0) as "avg_work_duration",
        NVL(AVG(AYRILMA_SURESI), 0) as "avg_leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    GROUP BY EGITIM_DURUMU
    ORDER BY "avg_work_duration" DESC
    """
    return oracle.execute_query(sql)

# 7. Detay Tablosu: Personel Listesi
@router.get("/engagement/details-table")
@cache(expire=300)
async def get_engagement_details(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company",
        ISYERI_ADI as "location",
        DEPARTMAN_KODU as "dept_code",
        CALISAN_ADI as "name",
        POZISYON as "position",
        CINSIYET as "gender",
        YAS as "age",
        MEDENI_DURUM as "status",
        EGITIM_DURUMU as "education",
        CALISMA_SURESI as "work_duration",
        AYRILMA_SURESI as "leave_duration"
    FROM IFSAPP.PERSONEL_CALISAN_BAGLILIGI_MV
    WHERE DIREKTORLUK_REF = '1'
    ORDER BY CALISMA_SURESI DESC
    FETCH FIRST 5000 ROWS ONLY
    """
    return oracle.execute_query(sql)




