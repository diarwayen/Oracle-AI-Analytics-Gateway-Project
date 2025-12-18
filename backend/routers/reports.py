from fastapi import APIRouter
from services import oracle

router = APIRouter()

@router.get("/top-sales")
def get_top_sales():
    """En çok satan 10 ürünü getiren sabit rapor"""
    sql = "SELECT product_name, amount FROM sales ORDER BY amount DESC FETCH FIRST 10 ROWS ONLY"
    return oracle.run_query(sql)

@router.get("/monthly-revenue")
def get_monthly_revenue():
    """Aylık ciro raporu"""
    sql = "SELECT SUM(amount) as total FROM sales WHERE sale_date > SYSDATE - 30"
    return oracle.run_query(sql)