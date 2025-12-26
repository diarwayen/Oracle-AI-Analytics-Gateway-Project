from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Location"])

# 1. Harita Verisi (İkamet İli - TR Kodlu)
@router.get("/location/map/residence")
@cache(expire=300)
async def get_map_residence(oracle: OracleService = Depends(get_oracle_service)):
    # TR-XX kodları Geomap için gereklidir
    sql = """
    SELECT 
        CASE 
            WHEN IKAMET_IL = 'ADANA' THEN 'TR-01'
            WHEN IKAMET_IL = 'ADIYAMAN' THEN 'TR-02'
            WHEN IKAMET_IL = 'ANKARA' THEN 'TR-06'
            WHEN IKAMET_IL = 'ANTALYA' THEN 'TR-07'
            WHEN IKAMET_IL = 'BURSA' THEN 'TR-16'
            WHEN IKAMET_IL = 'İSTANBUL' THEN 'TR-34'
            WHEN IKAMET_IL = 'İZMİR' THEN 'TR-35'
            WHEN IKAMET_IL = 'KOCAELİ' THEN 'TR-41'
            -- (Diğer iller buraya eklenebilir, şimdilik en popülerleri ve ELSE mantığı)
            ELSE 'TR-' || SUBSTR(IKAMET_IL, 1, 2) -- Basit bir fallback, gerekirse user'ın tam listesi eklenir
        END as "code",
        IKAMET_IL as "province",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY IKAMET_IL
    HAVING COUNT(CALISAN_ID) > 0
    """
    return oracle.execute_query(sql)

# 2. Harita Verisi (Görev İli - TR Kodlu)
@router.get("/location/map/duty")
@cache(expire=300)
async def get_map_duty(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        CASE 
            WHEN SEHIR = 'ADANA' THEN 'TR-01'
            WHEN SEHIR = 'ANKARA' THEN 'TR-06'
            WHEN SEHIR = 'İSTANBUL' THEN 'TR-34'
            WHEN SEHIR = 'İZMİR' THEN 'TR-35'
            ELSE SEHIR 
        END as "code",
        SEHIR as "province",
        COUNT(CALISAN_ID) as "count"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV
    WHERE AKTIF_CALISAN = 1 
      AND DIREKTORLUK_REF = '1' 
      AND CTURS = 1
    GROUP BY SEHIR
    HAVING COUNT(CALISAN_ID) > 0
    """
    return oracle.execute_query(sql)

# 3. İkamet İli Dağılımı (Sütun Grafik & Tablo)
@router.get("/location/residence-dist")
@cache(expire=300)
async def get_residence_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(IKAMET_IL, 'Bilinmiyor') as "province", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' AND AKTIF_CALISAN = 1 AND CTURS = 1 
    GROUP BY IKAMET_IL 
    ORDER BY "count" DESC
    FETCH FIRST 100 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 4. İşyeri Bazlı İkamet (Tablo)
@router.get("/location/table/residence-company")
@cache(expire=300)
async def get_table_residence(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", ISYERI_ADI as "location", 
        DEPARTMAN_ADI as "department", IKAMET_IL as "province", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' AND AKTIF_CALISAN = 1 AND CTURS = 1 
    GROUP BY SIRKET, ISYERI_ADI, DEPARTMAN_ADI, IKAMET_IL 
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 5. Görev Yeri Dağılımı (Sütun Grafik)
@router.get("/location/duty-dist")
@cache(expire=300)
async def get_duty_dist(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        NVL(SEHIR, 'Bilinmiyor') as "city", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' AND AKTIF_CALISAN = 1 AND CTURS = 1 
    GROUP BY SEHIR 
    ORDER BY "count" DESC
    """
    return oracle.execute_query(sql)

# 6. İşyeri Bazlı Görev Yeri (Tablo)
@router.get("/location/table/duty-company")
@cache(expire=300)
async def get_table_duty(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", ISYERI_ADI as "location", 
        DEPARTMAN_ADI as "department", SEHIR as "city", 
        COUNT(CALISAN_ID) as "count" 
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' AND AKTIF_CALISAN = 1 AND CTURS = 1 
    GROUP BY SIRKET, ISYERI_ADI, DEPARTMAN_ADI, SEHIR 
    ORDER BY "count" DESC
    FETCH FIRST 1000 ROWS ONLY
    """
    return oracle.execute_query(sql)

# 7. Büyük Çalışan Listesi (Full Tablo)
@router.get("/location/table/employee-list")
@cache(expire=300)
async def get_employee_list(oracle: OracleService = Depends(get_oracle_service)):
    sql = """
    SELECT 
        SIRKET as "company", CALISAN_ADI as "name", ISYERI_ADI as "location", 
        DEPARTMAN_ADI as "department", POZISYON as "position", 
        SEHIR as "duty_city", IKAMET_IL as "residence_city", IKAMET_MAHALLE as "district"
    FROM IFSAPP.PERSONEL_ORG_AGACI_MV 
    WHERE DIREKTORLUK_REF = '1' AND AKTIF_CALISAN = 1 AND CTURS = 1
    ORDER BY SIRKET, CALISAN_ADI
    FETCH FIRST 5000 ROWS ONLY
    """
    return oracle.execute_query(sql)
