from fastapi import APIRouter
from services import oracle
import random
from datetime import datetime, timedelta

router = APIRouter()

# --- SABİT RAPORLAR ---

@router.get("/top-sales")
def get_top_sales():
    """En çok satan 10 ürünü getiren rapor"""
    # DÜZELTME 1: Çok satırlı SQL için üç tırnak kullanıldı
    sql = """
    SELECT product_name, amount 
    FROM sales 
    ORDER BY amount DESC 
    FETCH FIRST 10 ROWS ONLY
    """
    return oracle.run_query(sql)

@router.get("/monthly-revenue")
def get_monthly_revenue():
    """Aylık ciro raporu"""
    # DÜZELTME 2: Üç tırnak kullanıldı
    sql = """
    SELECT SUM(amount) as total 
    FROM sales 
    WHERE sale_date > SYSDATE - 30
    """
    return oracle.run_query(sql)

# --- TEST ENDPOINT ---

@router.get("/mock-test")
def get_mock_data():
    """
    Grafana testi için rastgele veri üreten sahte endpoint.
    DB bağlantısı gerektirmez.
    """
    # DÜZELTME 3: Girintiler (Indentation) düzeltildi
    data = []
    categories = ["Elektronik", "Giyim", "Gıda", "Kırtasiye", "Otomotiv"]
    
    # Son 7 gün için rastgele veri üretelim
    for i in range(7):
        date_value = datetime.now() - timedelta(days=i)
        
        item = {
            "tarih": date_value.strftime("%Y-%m-%d"),
            "kategori": random.choice(categories),
            "satis_adedi": random.randint(10, 500),
            "ciro": random.randint(1000, 50000)
        }
        data.append(item)
    
    return data