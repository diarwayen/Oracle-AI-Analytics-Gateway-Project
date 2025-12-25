from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache # Redis önbellekleme
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["HR Fixed Reports"])

def execute_sql_report(query: str, oracle: OracleService):
    try:
        # SQL sorgusunu çalıştır ve sonucu döndür
        result = oracle.execute_query(query)
        return result
    except Exception as e:
        logger.error(f"Rapor Hatası: {str(e)}")
        return {"error": str(e)}

# --- RAPOR 1: DEPARTMAN DAĞILIMI ---
@router.get("/hr-department-stats")
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
    return execute_sql_report(sql, oracle)

# --- RAPOR 2: EĞİTİM DURUMU ---
@router.get("/hr-education-stats")
@cache(expire=300)
async def get_education_stats(oracle: OracleService = Depends(get_oracle_service)):
    # NOT: 0-9 arasındaki kodların karşılıklarını şirket standartlarına göre
    # aşağıdaki 'THEN' kısımlarından düzeltebilirsin.
    sql = """
    SELECT 
        CASE EGITIM_SEVIYESI
            WHEN '0' THEN 'Okur Yazar Değil'
            WHEN '1' THEN 'İlkokul'
            WHEN '2' THEN 'Ortaokul'
            WHEN '3' THEN 'Lise'
            WHEN '4' THEN 'Ön Lisans (MYO)'
            WHEN '5' THEN 'Lisans'
            WHEN '6' THEN 'Yüksek Lisans'
            WHEN '7' THEN 'Doktora'
            WHEN '8' THEN 'Doçent'
            WHEN '9' THEN 'Profesör'
            ELSE 'Diğer' 
        END as "category", 
        SUM(AKTIF_CALISAN) as "value"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1
      -- 'Bilgi Yok' olanları veya NULL olanları hariç tutuyoruz
      AND EGITIM_SEVIYESI IS NOT NULL 
      AND EGITIM_SEVIYESI NOT IN ('Bilgi Yok', 'Bilinmiyor', 'Tanımsız') 
      -- Sadece 0-9 arasını almak istersen şu satırı açabilirsin:
      -- AND EGITIM_SEVIYESI IN ('0','1','2','3','4','5','6','7','8','9')
    GROUP BY 
        CASE EGITIM_SEVIYESI
            WHEN '0' THEN 'Okur Yazar Değil'
            WHEN '1' THEN 'İlkokul'
            WHEN '2' THEN 'Ortaokul'
            WHEN '3' THEN 'Lise'
            WHEN '4' THEN 'Ön Lisans (MYO)'
            WHEN '5' THEN 'Lisans'
            WHEN '6' THEN 'Yüksek Lisans'
            WHEN '7' THEN 'Doktora'
            WHEN '8' THEN 'Doçent'
            WHEN '9' THEN 'Profesör'
            ELSE 'Diğer' 
        END
    ORDER BY "value" DESC
    """
    return execute_sql_report(sql, oracle)

# --- RAPOR 3: YAŞ ARALIĞI ---
@router.get("/hr-age-stats")
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
    return execute_sql_report(sql, oracle)



# --- RAPOR 4: CİNSİYET DAĞILIMI ---
@router.get("/hr-gender-stats")
@cache(expire=300)
async def get_gender_stats(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(CINSIYET, 'Belirtilmemiş') as "category",
        SUM(AKTIF_CALISAN) as "value"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1
    GROUP BY CINSIYET
    ORDER BY "value" DESC
    """
    return execute_sql_report(sql, oracle)

# --- RAPOR 5: İKAMET EDİLEN İL ---
@router.get("/hr-city-stats")
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
    return execute_sql_report(sql, oracle)

# --- RAPOR 6: PERSONEL GRUBU / STATÜ ---
@router.get("/hr-group-stats")
@cache(expire=300)
async def get_group_stats(oracle: OracleService = Depends(get_oracle_service)):
    # GRUP_ACIKLAMA genelde Mavi Yaka / Beyaz Yaka bilgisini tutar
    sql = """
    SELECT 
        NVL(GRUP_ACIKLAMA, 'Diğer') as "category",
        SUM(AKTIF_CALISAN) as "value"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1
    GROUP BY GRUP_ACIKLAMA
    ORDER BY "value" DESC
    """
    return execute_sql_report(sql, oracle)