from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["HR Training"])

# Ortak CTE (Common Table Expression) Mantığı
# Eğitim sorgularının %90'ı bu mantığı kullanıyor. Kod tekrarını önlemek için
# SQL içinde bunu tekrar tekrar kullanacağız.
BASE_TRAINING_CTE = """
WITH CPA_MATCH AS (
    SELECT 
        cpa.emp_no, cpa.company_id, cpa.org_code, cpa.pos_code,
        cpa.valid_from, cpa.valid_to, cpa.primary, x.training_event_id,
        ROW_NUMBER() OVER (
            PARTITION BY cpa.emp_no, cpa.company_id, x.training_event_id
            ORDER BY
                CASE WHEN x.start_date BETWEEN cpa.valid_from AND cpa.valid_to AND cpa.org_code != '001' THEN 1 ELSE 2 END,
                CASE WHEN cpa.primary = 1 THEN 1 ELSE 2 END,
                cpa.valid_to DESC
        ) rn
    FROM company_pers_assign cpa
    JOIN training_participant p ON p.participant_id = cpa.emp_no
    JOIN training_event x ON x.training_event_id = p.training_event_id
),
MAIN_DATA AS (
    SELECT 
        x.training_event_id AS EGITIM_ID,
        NVL(x.training_event_name,'Bilgi Girilmemiş') AS EGITIM_ADI,
        NVL(COURSE_API.GET_COURSE_TITLE(c.course_id), 'Bilgi Girilmemiş') AS EGITIM_KATEGORI_ADI,
        NVL(COURSE_CATEGORY_API.GET_COURSE_CATEGORY_NAME(COURSE_API.GET_COURSE_CATEGORY_ID(c.course_id)), 'Bilgi Girilmemiş') AS EGITIM_ALAN_ADI,
        x.start_date AS EGITIM_BASLANGIC_TARIHI,
        x.end_date AS EGITIM_BITIS_TARIHI,
        p.cancel_date AS IPTAL_TARIHI,
        
        -- Süre Hesaplamaları
        CASE
            WHEN x.training_duration_unit = 'Day'  THEN x.training_duration * 8
            WHEN x.training_duration_unit = 'Hour' THEN x.training_duration
        END AS EGITIM_SURESI_SAAT,
        
        -- Kişi Başına Düşen Süre (İptal edilmeyenlere bölünür)
        CASE 
            WHEN p.cancel_date IS NULL AND SUM(CASE WHEN p.cancel_date IS NULL THEN 1 ELSE 0 END) OVER (PARTITION BY x.training_event_id) > 0
            THEN (CASE WHEN x.training_duration_unit = 'Day' THEN x.training_duration * 8 WHEN x.training_duration_unit = 'Hour' THEN x.training_duration END) 
                 / SUM(CASE WHEN p.cancel_date IS NULL THEN 1 ELSE 0 END) OVER (PARTITION BY x.training_event_id)
            ELSE 0
        END AS KISI_BASINA_DUSEN_EGITIM_SAATI,

        x.company_id AS SIRKET,
        p.participant_id AS KATILIMCI_ID,
        -- Unique ID Mantığı
        p.participant_id || CASE WHEN p.participant_type = 'Internal' THEN 'DAHİLİ' ELSE 'HARİCİ' END AS KATILIMCI_ID_UNIQUE,
        p.participant_name AS KATILIMCI_ADI,
        
        -- Aktiflik Kontrolü
        CASE WHEN p.participant_type = 'Internal' AND EXISTS (
                SELECT 1 FROM trbrd_personel_calisma_tab t
                WHERE t.emp_no = p.participant_id AND t.company_id = x.company_id
                AND t.baslama_tarihi <= SYSDATE AND (t.BITIS_TARIHI IS NULL OR t.BITIS_TARIHI > SYSDATE)
            ) THEN 1 ELSE 0 END AS AKTIF_CALISAN,
            
        CASE WHEN p.participant_type = 'Internal' THEN 'DAHİLİ' ELSE 'HARİCİ' END AS KATILIMCI_TIPI,
        
        -- Pozisyon ve Departman
        CASE WHEN p.participant_type = 'Internal' THEN UPPER(NVL(COMPANY_POSITION_API.GET_POSITION_TITLE(x.company_id, cpa.pos_code),'BİLGİ GİRİLMEMİŞ')) ELSE 'HARİCİ KATILIMCI' END AS KATILIMCI_UNVAN,
        CASE WHEN p.participant_type = 'External' THEN 'PETLAS' ELSE nvl(UPPER(COMPANY_ORG_API.Get_Org_Name(X.company_id, cpa.org_code) ),'BİLGİ GİRİLMEMİŞ!!') END AS DEPARTMAN_ADI,
        
        -- Grup Bilgileri
        CASE WHEN p.participant_type = 'Internal' THEN nvl(IFSAPP.TRBRD_CALISAN_GRUBU_API.Get_Aciklama(TRBD.company_id, TRBD.isyeri_kodu, IFSAPP.TRBRD_PERSONEL_SICIL_api.Get_Grup_Kodu(TRBD.company_id, TRBD.emp_no, TRBD.seq_no, IFSAPP.TRBRD_PERSONEL_CALISMA_API.GET_AKTIF_SATIR_NO(TRBD.company_id, TRBD.emp_no, TRBD.seq_no))),'Bilgi Yok!') ELSE 'HARİCİ KATILIMCI' END AS GRUP_ACIKLAMA

    FROM training_event x
    LEFT JOIN training_event_course c ON c.training_event_id = x.training_event_id
    LEFT JOIN training_participant p ON p.training_event_id = x.training_event_id
    LEFT JOIN CPA_MATCH cpa ON cpa.emp_no = p.participant_id AND cpa.company_id = x.company_id AND cpa.training_event_id = x.training_event_id AND cpa.rn = 1
    LEFT JOIN trbrd_personel_calisma_tab TRBD ON TRBD.EMP_NO = CPA.emp_no AND CPA.company_id = TRBD.company_id AND X.start_date BETWEEN TRBD.BASLAMA_TARIHI AND NVL(TRBD.BITIS_TARIHI,DATE '2999-12-31')
)
"""

# 1. KPI Kartları (Tek Sorguda Toplamalar)
@router.get("/hr_training/kpi-summary")
@cache(expire=300)
async def get_training_kpi(oracle: OracleService = Depends(get_oracle_service)):
    sql = BASE_TRAINING_CTE + """
    SELECT 
        -- 1. Toplam Katılımcı (Unique ID bazlı)
        COUNT(CASE WHEN IPTAL_TARIHI IS NULL THEN KATILIMCI_ID_UNIQUE END) as "total_participants",
        
        -- 2. Benzersiz Katılımcı
        COUNT(DISTINCT CASE WHEN IPTAL_TARIHI IS NULL THEN KATILIMCI_ID_UNIQUE END) as "unique_participants",
        
        -- 3. Toplam Katılımcı (Aktif & Dahili)
        COUNT(CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'DAHİLİ' AND AKTIF_CALISAN = 1 THEN KATILIMCI_ID_UNIQUE END) as "active_internal_total",
        
        -- 4. Benzersiz Katılımcı (Aktif & Dahili) - İstenilen "fd04..." kodu yerine anlamlı isim
        COUNT(DISTINCT CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'DAHİLİ' AND AKTIF_CALISAN = 1 THEN KATILIMCI_ID_UNIQUE END) as "active_internal_unique",
        
        -- 5. Benzersiz Harici Katılımcı
        COUNT(DISTINCT CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'HARİCİ' THEN KATILIMCI_ID_UNIQUE END) as "external_unique",
        
        -- 6. Toplam Eğitim Saati
        ROUND(SUM(CASE WHEN IPTAL_TARIHI IS NULL THEN KISI_BASINA_DUSEN_EGITIM_SAATI ELSE 0 END), 2) as "total_training_hours",
        
        -- 7. Katılımcı Başına Düşen Eğitim Saati (Sadece Dahili ve Aktif)
        ROUND(
            SUM(CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'DAHİLİ' AND AKTIF_CALISAN = 1 THEN EGITIM_SURESI_SAAT ELSE 0 END)
            /
            NULLIF(COUNT(CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'DAHİLİ' AND AKTIF_CALISAN = 1 THEN KATILIMCI_ID_UNIQUE END), 0)
        , 2) as "avg_hours_per_active_internal",
        
        -- 8. Harici Katılımcı Başına Eğitim Saati
        ROUND(
            SUM(CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'HARİCİ' THEN EGITIM_SURESI_SAAT ELSE 0 END)
            /
            NULLIF(COUNT(CASE WHEN IPTAL_TARIHI IS NULL AND KATILIMCI_TIPI = 'HARİCİ' THEN KATILIMCI_ID_UNIQUE END), 0)
        , 2) as "avg_hours_per_external"

    FROM MAIN_DATA
    """
    return oracle.execute_query(sql)

# 2. Eğitim İstatistikleri (Toplam Eğitim Sayısı vb.)
@router.get("/hr_training/stats/counts")
@cache(expire=300)
async def get_training_counts(oracle: OracleService = Depends(get_oracle_service)):
    sql = BASE_TRAINING_CTE + """
    SELECT 
        COUNT(DISTINCT EGITIM_ID) as "total_trainings_count"
    FROM MAIN_DATA
    WHERE IPTAL_TARIHI IS NULL
    """
    return oracle.execute_query(sql)

# 3. Grafik: En Çok Verilen Eğitimler (Top 10)
@router.get("/hr_training/charts/top-trainings")
@cache(expire=300)
async def get_top_trainings(oracle: OracleService = Depends(get_oracle_service)):
    sql = BASE_TRAINING_CTE + """
    SELECT 
        EGITIM_ADI as "training_name",
        COUNT(DISTINCT EGITIM_ID) as "count"
    FROM MAIN_DATA
    WHERE IPTAL_TARIHI IS NULL
    GROUP BY EGITIM_ADI
    ORDER BY "count" DESC
    FETCH FIRST 10 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 4. Grafik: Aylara Göre Eğitim Sayısı
@router.get("/hr_training/charts/monthly-trend")
@cache(expire=300)
async def get_monthly_training_trend(oracle: OracleService = Depends(get_oracle_service)):
    sql = BASE_TRAINING_CTE + """
    SELECT 
        TO_CHAR(TRUNC(EGITIM_BASLANGIC_TARIHI, 'MONTH'), 'YYYY-MM') as "month",
        COUNT(DISTINCT EGITIM_ID) as "count"
    FROM MAIN_DATA
    WHERE IPTAL_TARIHI IS NULL
    GROUP BY TRUNC(EGITIM_BASLANGIC_TARIHI, 'MONTH')
    ORDER BY "month" DESC
    FETCH FIRST 24 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 5. Tablolar: Kırılımlar (Pozisyon, Departman, Kategori, Alan, Grup)
@router.get("/hr_training/breakdown/{category}")
@cache(expire=300)
async def get_training_breakdown(category: str, oracle: OracleService = Depends(get_oracle_service)):
    # Kategoriye göre dinamik kolon seçimi
    col_map = {
        "position": "KATILIMCI_UNVAN",
        "department": "DEPARTMAN_ADI",
        "group": "GRUP_ACIKLAMA",
        "category": "EGITIM_KATEGORI_ADI",
        "area": "EGITIM_ALAN_ADI"
    }
    
    if category not in col_map:
        return {"error": "Invalid category. Options: position, department, group, category, area"}
    
    target_col = col_map[category]
    
    sql = BASE_TRAINING_CTE + f"""
    SELECT 
        {target_col} as "name",
        COUNT(DISTINCT KATILIMCI_ID) as "participant_count", -- Kişi sayısı
        COUNT(DISTINCT EGITIM_ID) as "training_count"       -- Eğitim sayısı
    FROM MAIN_DATA
    WHERE IPTAL_TARIHI IS NULL
    GROUP BY {target_col}
    ORDER BY "participant_count" DESC
    FETCH FIRST 100 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 6. Liste: Eğitim Takvimi (Gelecek Eğitimler)
@router.get("/hr_training/calendar")
@cache(expire=300)
async def get_training_calendar(oracle: OracleService = Depends(get_oracle_service)):
    sql = BASE_TRAINING_CTE + """
    SELECT DISTINCT
        TRUNC(EGITIM_BASLANGIC_TARIHI) as "start_date",
        EGITIM_ID as "id",
        EGITIM_ADI as "title",
        EGITIM_BITIS_TARIHI as "end_date",
        SIRKET as "company"
    FROM MAIN_DATA
    WHERE IPTAL_TARIHI IS NULL 
      AND TRUNC(EGITIM_BASLANGIC_TARIHI) > TRUNC(SYSDATE)
    ORDER BY "start_date" ASC
    FETCH FIRST 50 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 7. Liste: Eğitim Almayan Personeller
@router.get("/hr_training/no-training-list")
@cache(expire=300)
async def get_no_training_employees(oracle: OracleService = Depends(get_oracle_service)):
    # Bu sorgu farklı bir mantıkta olduğu için CTE kullanmıyoruz, direkt view'den joinliyoruz
    sql = """
    SELECT 
        P.SIRKET as "company",
        P.ISYERI_ADI as "location",
        P.DEPARTMAN_ADI as "department",
        P.POZISYON_ACIKLAMASI as "position",
        P.CALISAN_ID as "emp_id",
        P.CALISAN_ADI as "full_name"
    FROM PERSONEL_ORG_AGACI_MV P    
    LEFT JOIN TRAINING_PARTICIPANT_QRY X ON P.CALISAN_ID = X.PARTICIPANT_ID
    WHERE X.PARTICIPANT_ID IS NULL 
      AND P.DIREKTORLUK_REF = '1'
      AND P.AKTIF_CALISAN = 1
    ORDER BY P.SIRKET, P.DEPARTMAN_ADI
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 7.1 Eğitim Almayan Personel Sayısı
@router.get("/hr_training/no-training-count")
@cache(expire=300)
async def get_no_training_count(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT COUNT(DISTINCT P.CALISAN_ID) as "count"
    FROM PERSONEL_ORG_AGACI_MV P    
    LEFT JOIN TRAINING_PARTICIPANT_QRY X ON P.CALISAN_ID = X.PARTICIPANT_ID
    WHERE X.PARTICIPANT_ID IS NULL 
      AND P.DIREKTORLUK_REF = '1'
      AND P.AKTIF_CALISAN = 1
    """
    return oracle.execute_query(sql)

# 8. Full Detay Tablosu (Infinity Table için)
@router.get("/hr_training/full-details")
@cache(expire=300)
async def get_full_training_details(oracle: OracleService = Depends(get_oracle_service)):
    sql = BASE_TRAINING_CTE + """
    SELECT * FROM MAIN_DATA
    ORDER BY EGITIM_BASLANGIC_TARIHI DESC
    FETCH FIRST 2000 ROWS ONLY
    """
    return oracle.execute_query(sql)




