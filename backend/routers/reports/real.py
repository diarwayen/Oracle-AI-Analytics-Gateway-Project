from fastapi import APIRouter, Depends
from services.oracle import OracleService
from core.deps import get_oracle_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports DB"])


def execute_sql_report(query: str, oracle: OracleService, params: dict = None):
    try:
        result = oracle.execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"DB Rapor Hatası: {str(e)}")
        return {"error": str(e), "detail": "Lütfen /reports/setup-db adresine giderek tabloları oluşturun."}


@router.get("/db-sales-trend")
async def real_sales_trend(oracle=Depends(get_oracle_service)):
    sql = """
    SELECT 
        TO_CHAR(satis_tarihi, 'YYYY-MM-DD') as "date",
        SUM(toplam_tutar) as "amount",
        COUNT(*) as "order_count"
    FROM satislar
    GROUP BY TO_CHAR(satis_tarihi, 'YYYY-MM-DD')
    ORDER BY 1
    """
    return execute_sql_report(sql, oracle)


@router.get("/db-category-distribution")
async def real_category_dist(oracle=Depends(get_oracle_service)):
    sql = """
    SELECT 
        u.kategori as "category",
        SUM(s.toplam_tutar) as "value"
    FROM satislar s
    JOIN urunler u ON s.urun_id = u.id
    GROUP BY u.kategori
    ORDER BY 2 DESC
    """
    return execute_sql_report(sql, oracle)


@router.get("/db-kpi")
async def real_kpi(oracle=Depends(get_oracle_service)):
    kpi_data = {}
    try:
        try:
            res1 = oracle.execute_query("SELECT SUM(toplam_tutar) as VAL FROM satislar")
            kpi_data["current_revenue"] = res1[0]["VAL"] if isinstance(res1, list) and res1 and res1[0]["VAL"] else 0
        except Exception:
            kpi_data["current_revenue"] = 0

        try:
            res2 = oracle.execute_query("SELECT COUNT(*) as VAL FROM satislar")
            kpi_data["active_users"] = res2[0]["VAL"] if isinstance(res2, list) and res2 else 0
        except Exception:
            kpi_data["active_users"] = 0

        try:
            res3 = oracle.execute_query("SELECT COUNT(*) as VAL FROM urunler")
            kpi_data["ai_token_usage"] = res3[0]["VAL"] if isinstance(res3, list) and res3 else 0
        except Exception:
            kpi_data["ai_token_usage"] = 0

        kpi_data["monthly_revenue_target"] = 100000

    except Exception as e:
        logger.error(f"KPI DB Hatası: {e}")
        return {"error": str(e)}

    return kpi_data


@router.get("/db-transactions")
async def real_transactions(oracle=Depends(get_oracle_service)):
    sql = """
    SELECT 
        s.id,
        u.urun_adi as "product",
        s.toplam_tutar as "amount",
        TO_CHAR(s.satis_tarihi, 'YYYY-MM-DD HH24:MI:SS') as "timestamp",
        'Completed' as "status" 
    FROM satislar s
    JOIN urunler u ON s.urun_id = u.id
    ORDER BY s.satis_tarihi DESC
    FETCH FIRST 20 ROWS ONLY
    """
    return execute_sql_report(sql, oracle)



