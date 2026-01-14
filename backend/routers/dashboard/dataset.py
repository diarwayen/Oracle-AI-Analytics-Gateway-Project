from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
from fastapi_cache.decorator import cache

router = APIRouter(tags=["Dataset"])


@router.get("/dataset/full")
@cache(expire=30) 
async def get_full_dataset(oracle: OracleService = Depends(get_oracle_service)):

    sql = """
    SELECT 
        t.*, 
        
        ROUND(DBMS_RANDOM.VALUE(1, 20), 2) as "work_duration_years",
        ROUND(DBMS_RANDOM.VALUE(0, 5), 1) as "leave_duration_years",
        ROUND(DBMS_RANDOM.VALUE(10, 100), 0) as "performance_score"

    FROM IFSAPP.PERSONEL_ORG_AGACI_MV t
    WHERE t.DIREKTORLUK_REF = '1'
      AND t.AKTIF_CALISAN = 1 
      AND t.CTURS = 1
      
     FETCH FIRST 2000 ROWS ONLY
    """
    return oracle.execute_query(sql)