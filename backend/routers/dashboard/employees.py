from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

# Endpointlerin tag'i
router = APIRouter(tags=["Employees"])

# ----------------------------------------------------------------
# 1. KPI KARTLARI (ÖZET METRİKLER)
# ----------------------------------------------------------------


@router.get("/employees/kpi-summary")
@cache(expire=300)
async def get_kpi_summary(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        -- 1. Toplam Çalışan
        SUM(CASE WHEN AKTIF_CALISAN = 1 THEN 1 ELSE 0 END) as "total_active",
        
        -- 2. İşe Başlayan (Flag 1 ise)
        SUM(CASE WHEN ISE_BASLAYAN = 1 THEN 1 ELSE 0 END) as "new_hires",
        
        -- 3. İşten Ayrılan (Flag 1 ise)
        SUM(CASE WHEN ISTEN_AYRILAN = 1 THEN 1 ELSE 0 END) as "leavers",
        
        -- 4. Erkek Çalışan
        SUM(CASE WHEN AKTIF_CALISAN = 1 AND CINSIYET = 'ERKEK' THEN 1 ELSE 0 END) as "total_male",
        
        -- 5. Kadın Çalışan
        SUM(CASE WHEN AKTIF_CALISAN = 1 AND CINSIYET = 'KADIN' THEN 1 ELSE 0 END) as "total_female",
        
        -- 6. Engelli Personel
        SUM(CASE WHEN AKTIF_CALISAN = 1 AND ENGELLI_PERSONEL = 1 THEN 1 ELSE 0 END) as "total_disabled",
        
        -- EK 1: Yaş Ortalaması
        ROUND(AVG(CASE WHEN AKTIF_CALISAN = 1 THEN YAS END), 1) as "avg_age",
        
        -- EK 2: Kadın Oranı (%)
        ROUND(
            (SUM(CASE WHEN AKTIF_CALISAN = 1 AND CINSIYET = 'KADIN' THEN 1 ELSE 0 END) / 
             NULLIF(SUM(CASE WHEN AKTIF_CALISAN = 1 THEN 1 ELSE 0 END), 0)
            ) * 100, 1
        ) as "female_ratio"

    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 2. GRAFİKLER VE DAĞILIMLAR
# ----------------------------------------------------------------

# Metrik 8: Pozisyonlara Göre Dağılım
@router.get("/employees/distribution/position")
@cache(expire=300)
async def get_dist_position(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        POZISYON as "position", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY POZISYON 
    ORDER BY "count" DESC
    FETCH FIRST 100 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 9 & 13: İşyeri Bazlı Dağılım
@router.get("/employees/distribution/location")
@cache(expire=300)
async def get_dist_location(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        ISYERI_ADI as "location", 
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY ISYERI_ADI 
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# Metrik 10 & 12: Şirket Bazlı Dağılım
@router.get("/employees/distribution/company")
@cache(expire=300)
async def get_dist_company(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", 
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY SIRKET 
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# EK Metrik: Yaka Dağılımı (Mavi/Beyaz)
@router.get("/employees/distribution/collar")
@cache(expire=300)
async def get_dist_collar(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(GRUP_ACIKLAMA, 'Diğer') as "collar_type",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1
    GROUP BY GRUP_ACIKLAMA
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# EK Metrik: Medeni Durum
@router.get("/employees/distribution/marital")
@cache(expire=300)
async def get_dist_marital(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(MEDENI_DURUM, 'Bilinmiyor') as "status",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1
    GROUP BY MEDENI_DURUM
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# EK Metrik: Çalışma Statüsü (Kadrolu/Sözleşmeli)
@router.get("/employees/distribution/employment-status")
@cache(expire=300)
async def get_dist_employment_status(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(STATU, 'Diğer') as "status",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1
    GROUP BY STATU
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# ----------------------------------------------------------------
# 3. DETAYLI TABLOLAR (SEARCH BAR İÇERENLER)
# ----------------------------------------------------------------

# Metrik 7: İşyeri Bazlı Engelli Personel Detayı
@router.get("/employees/details/disabled")
@cache(expire=300)
async def get_details_disabled(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        ISYERI_ADI as "location", 
        DEPARTMAN_ADI as "department", 
        POZISYON as "position", 
        ENGEL_DERECESI as "disability_degree", 
        CINSIYET as "gender", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND ENGELLI_PERSONEL = 1 
      AND CTURS = 1 
    GROUP BY ISYERI_ADI, DEPARTMAN_ADI, POZISYON, ENGEL_DERECESI, CINSIYET 
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 11: Görev Yeri Bazlı Çalışanlar
@router.get("/employees/details/duty-place")
@cache(expire=300)
async def get_details_duty_place(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(GOREV_YERI, 'GÖREV YERİ BİLGİSİ YOK') as "duty_place", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY NVL(GOREV_YERI, 'GÖREV YERİ BİLGİSİ YOK') 
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 14: Şirket ve Pozisyon Bazlı
@router.get("/employees/details/company-position")
@cache(expire=300)
async def get_details_company_position(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", 
        ISYERI_ADI as "location", 
        NVL(POZISYON, 'POZISYON BİLGİSİ YOK') as "position", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY SIRKET, ISYERI_ADI, NVL(POZISYON, 'POZISYON BİLGİSİ YOK') 
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 15: Şirket, Cinsiyet ve Eğitim
@router.get("/employees/details/demographics-basic")
@cache(expire=300)
async def get_details_demographics_basic(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", 
        ISYERI_ADI as "location", 
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education", 
        CINSIYET as "gender", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY SIRKET, ISYERI_ADI, NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ'), CINSIYET 
    ORDER BY SIRKET, "education" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# Metrik 16: Şirket, Pozisyon, Cinsiyet ve Eğitim (En Detaylı)
@router.get("/employees/details/demographics-full")
@cache(expire=300)
async def get_details_demographics_full(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", 
        ISYERI_ADI as "location", 
        NVL(POZISYON, 'POZISYON BİLGİSİ BOŞ') as "position", 
        CINSIYET as "gender", 
        NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') as "education", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' 
      AND AKTIF_CALISAN = 1 
      AND CTURS = 1 
    GROUP BY SIRKET, ISYERI_ADI, NVL(POZISYON, 'POZISYON BİLGİSİ BOŞ'), CINSIYET, NVL(EGITIM_DURUMU, 'EĞİTİM BİLGİSİ BOŞ') 
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)


# --- RAPOR 1: DEPARTMAN DAĞILIMI ---
@router.get("/employees/details/department-stats")
@cache(expire=300) # 5 dakika cache
async def get_department_stats(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        DEPARTMAN_ADI as "category", 
        SUM(AKTIF_CALISAN) as "value"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1
    GROUP BY DEPARTMAN_ADI
    ORDER BY "value" DESC
    FETCH FIRST 15 ROWS ONLY
    """
    return oracle.execute_query(sql)


# --- RAPOR 3: YAŞ ARALIĞI ---
@router.get("/employees/details/age-stats")
@cache(expire=300)
async def get_age_stats(oracle: OracleService = Depends(get_oracle_service)):
    # YAS_ARALIGI kolonu doluysa onu kullanır, boşsa YAS kolonundan biz hesaplarız
    sql = """
    SELECT 
        NVL(YAS_ARALIGI, 
            CASE 
                WHEN YAS < 20 THEN '20 Altı'
                WHEN YAS BETWEEN 20 AND 29 THEN '20-29 Yaş'
                WHEN YAS BETWEEN 30 AND 39 THEN '30-39 Yaş'
                WHEN YAS BETWEEN 40 AND 49 THEN '40-49 Yaş'
                WHEN YAS >= 50 THEN '50 Üzeri'
                ELSE 'Bilinmiyor'
            END
        ) as "category",
        SUM(AKTIF_CALISAN) as "value"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1
    GROUP BY NVL(YAS_ARALIGI, 
            CASE 
                WHEN YAS < 20 THEN '20 Altı'
                WHEN YAS BETWEEN 20 AND 29 THEN '20-29 Yaş'
                WHEN YAS BETWEEN 30 AND 39 THEN '30-39 Yaş'
                WHEN YAS BETWEEN 40 AND 49 THEN '40-49 Yaş'
                WHEN YAS >= 50 THEN '50 Üzeri'
                ELSE 'Bilinmiyor'
            END)
    ORDER BY "category"
    """
    return oracle.execute_query(sql)



# --- RAPOR 5: İKAMET EDİLEN İL ---
@router.get("/employees/details/city-stats")
@cache(expire=300)
async def get_city_stats(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(IKAMET_IL, 'Bilinmiyor') as "category",
        SUM(AKTIF_CALISAN) as "value"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1
    -- "BİLGİ GİRİLMEMİŞ!!" olan satırları hariç tutuyoruz:
    AND IKAMET_IL <> 'BİLGİ GİRİLMEMİŞ!!' 
    AND IKAMET_IL IS NOT NULL
    GROUP BY IKAMET_IL
    ORDER BY "value" DESC
    FETCH FIRST 10 ROWS ONLY
    """
    return oracle.execute_query(sql)