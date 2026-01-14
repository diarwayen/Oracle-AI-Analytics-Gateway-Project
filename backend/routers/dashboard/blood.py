from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Blood"])

# ----------------------------------------------------------------
# 1. KPI KARTLARI (TÜM STATLAR TEK SORGUDA)
# ----------------------------------------------------------------
@router.get("/blood/kpi-summary")
@cache(expire=300)
async def get_blood_kpi(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        -- Toplam Çalışan
        COUNT(CALISAN_ID) as "total",
        
        -- Pozitif Gruplar
        SUM(CASE WHEN KAN_GRUBU = 'A+' THEN 1 ELSE 0 END) as "a_pos",
        SUM(CASE WHEN KAN_GRUBU = 'B+' THEN 1 ELSE 0 END) as "b_pos",
        SUM(CASE WHEN KAN_GRUBU = 'AB+' THEN 1 ELSE 0 END) as "ab_pos",
        SUM(CASE WHEN KAN_GRUBU = 'O+' THEN 1 ELSE 0 END) as "o_pos",
        
        -- Negatif Gruplar
        SUM(CASE WHEN KAN_GRUBU = 'A-' THEN 1 ELSE 0 END) as "a_neg",
        SUM(CASE WHEN KAN_GRUBU = 'B-' THEN 1 ELSE 0 END) as "b_neg",
        SUM(CASE WHEN KAN_GRUBU = 'AB-' THEN 1 ELSE 0 END) as "ab_neg",
        SUM(CASE WHEN KAN_GRUBU = 'O-' THEN 1 ELSE 0 END) as "o_neg",
        
        -- Bilgi Girilmemiş (Null veya Boş)
        SUM(CASE WHEN KAN_GRUBU IS NULL OR KAN_GRUBU = 'BİLGİ GİRİLMEMİŞ!!' THEN 1 ELSE 0 END) as "unknown"
        
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 2. GRAFİKLER (Pie, Bar, Heatmap)
# ----------------------------------------------------------------

# Grafik 1: Kan Grubu Dağılımı (Pie Chart)
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

# Grafik 2: Cinsiyet Dağılımı (Bar Chart)
@router.get("/blood/gender-distribution")
@cache(expire=300)
async def get_gender_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        CINSIYET as "gender", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
    GROUP BY CINSIYET
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# Grafik 3: Kan Grubu ve Yaş Aralığı (Grouped Bar Chart)
@router.get("/blood/age-distribution")
@cache(expire=300)
async def get_blood_age_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        KAN_GRUBU as "blood_type",
        NVL(YAS_ARALIGI, 'Bilinmiyor') as "age_group",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
      -- GÜNCELLENEN KISIM: Hem boşlukları temizliyoruz hem de NULL kontrolü yapıyoruz
      AND TRIM(KAN_GRUBU) <> 'BİLGİ GİRİLMEMİŞ!!' 
      AND KAN_GRUBU IS NOT NULL
    GROUP BY KAN_GRUBU, NVL(YAS_ARALIGI, 'Bilinmiyor')
    ORDER BY "blood_type", "age_group"
    """
    return oracle.execute_query(sql)

# Grafik 4: Şirket Bazlı Kan Grubu (Heatmap)
@router.get("/blood/company-heatmap")
@cache(expire=300)
async def get_company_blood_heatmap(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company",
        NVL(KAN_GRUBU, 'Bilinmiyor') as "blood_type",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1 
    GROUP BY SIRKET, NVL(KAN_GRUBU, 'Bilinmiyor')
    ORDER BY SIRKET, "count" DESC
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 3. DETAYLI TABLO
# ----------------------------------------------------------------

# Tablo: İşyeri, Kan Grubu ve Cinsiyet Kırılımı
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