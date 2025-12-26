from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

# Endpoint tag'i
router = APIRouter(tags=["Education"])

# ----------------------------------------------------------------
# 1. KPI KARTLARI (İLK 12 METRİK TEK SORGUDA)
# ----------------------------------------------------------------
# URL: /api/education/kpi-summary
@router.get("/education/kpi-summary")
@cache(expire=300)
async def get_education_kpi_summary(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        COUNT(CALISAN_ID) as "total_employees",
        SUM(CASE WHEN EGITIM_DURUMU = 'DOKTORA' THEN 1 ELSE 0 END) as "phd",
        SUM(CASE WHEN EGITIM_DURUMU = 'YÜKSEK LİSANS' THEN 1 ELSE 0 END) as "master",
        SUM(CASE WHEN EGITIM_DURUMU = 'LİSANS' THEN 1 ELSE 0 END) as "bachelor",
        SUM(CASE WHEN EGITIM_DURUMU = 'ÖN LİSANS' THEN 1 ELSE 0 END) as "associate",
        SUM(CASE WHEN EGITIM_DURUMU = 'LİSE' THEN 1 ELSE 0 END) as "high_school",
        SUM(CASE WHEN EGITIM_DURUMU = 'MESLEK LİSESİ' THEN 1 ELSE 0 END) as "vocational_high_school",
        SUM(CASE WHEN EGITIM_DURUMU = 'İLKÖĞRETİM' THEN 1 ELSE 0 END) as "primary_education",
        SUM(CASE WHEN EGITIM_DURUMU = 'ORTAOKUL' THEN 1 ELSE 0 END) as "middle_school",
        SUM(CASE WHEN EGITIM_DURUMU = 'İLKOKUL' THEN 1 ELSE 0 END) as "primary_school",
        SUM(CASE WHEN EGITIM_DURUMU = 'OKUR YAZAR' THEN 1 ELSE 0 END) as "literate",
        SUM(CASE WHEN EGITIM_DURUMU IS NULL OR EGITIM_DURUMU = 'BİLGİ GİRİLMEMİŞ!!' THEN 1 ELSE 0 END) as "no_info"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 2. GRAFİKLER (HEATMAP & BAR CHARTS)
# ----------------------------------------------------------------

# Metrik 13: Yaş Dağılımına Göre Eğitim (Heatmap)
# URL: /api/education/charts/age-heatmap
@router.get("/education/charts/age-heatmap")
@cache(expire=300)
async def get_age_education_heatmap(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(EGITIM_DURUMU, 'Bilinmiyor') as "education", 
        NVL(YAS_ARALIGI, 'Diğer') as "age_group", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY NVL(EGITIM_DURUMU, 'Bilinmiyor'), NVL(YAS_ARALIGI, 'Diğer')
    ORDER BY "education" ASC, "age_group" DESC
    """
    return oracle.execute_query(sql)

# Metrik 14: Eğitim Durumu Dağılımı (Sütun Grafik)
# URL: /api/education/charts/level-distribution
@router.get("/education/charts/level-distribution")
@cache(expire=300)
async def get_education_level_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education",
        COUNT(CALISAN_ID) as "count",
        MIN(EGITIM_SEVIYESI) as "level_code"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ')
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# Metrik 15: Cinsiyet Bazlı Eğitim Durumu (İkili Sütun Grafik)
# URL: /api/education/charts/gender-distribution
@router.get("/education/charts/gender-distribution")
@cache(expire=300)
async def get_education_gender_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ'), CINSIYET
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 3. DETAYLI TABLOLAR (SEARCH BAR'LI)
# ----------------------------------------------------------------

# Metrik 16: İşyeri & Cinsiyet Bazlı
# URL: /api/education/tables/location-gender
@router.get("/education/tables/location-gender")
@cache(expire=300)
async def get_table_location_gender(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company",
        ISYERI_ADI as "location",
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY SIRKET, ISYERI_ADI, NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ'), CINSIYET
    ORDER BY ISYERI_ADI ASC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 17: Departman Bazlı
# URL: /api/education/tables/department
@router.get("/education/tables/department")
@cache(expire=300)
async def get_table_department(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company",
        ISYERI_ADI as "location",
        DEPARTMAN_ADI as "department",
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY SIRKET, ISYERI_ADI, DEPARTMAN_ADI, NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ'), CINSIYET
    ORDER BY SIRKET, ISYERI_ADI DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 18: Pozisyon & İşyeri Bazlı
# URL: /api/education/tables/position-location
@router.get("/education/tables/position-location")
@cache(expire=300)
async def get_table_position_location(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company",
        ISYERI_ADI as "location",
        POZISYON as "position",
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY SIRKET, ISYERI_ADI, POZISYON, NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ'), CINSIYET
    ORDER BY POZISYON, CINSIYET DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 19: Sadece Pozisyon Bazlı
# URL: /api/education/tables/position
@router.get("/education/tables/position")
@cache(expire=300)
async def get_table_position(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(POZISYON, 'POZİSYON BİLGİSİ BOŞ') as "position",
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education",
        CINSIYET as "gender",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY NVL(POZISYON, 'POZİSYON BİLGİSİ BOŞ'), NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ'), CINSIYET
    ORDER BY "position", "gender" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)
