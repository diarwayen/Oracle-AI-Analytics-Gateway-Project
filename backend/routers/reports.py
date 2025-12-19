from fastapi import APIRouter, Depends
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta
import logging

# Not: llm_service importu SİLİNDİ (Hata sebebiydi)
# Not: OracleService importu şimdilik kalsın ama kullanmıyoruz, mock veri dönüyoruz.

# Logger
logger = logging.getLogger(__name__)

router = APIRouter()

# --- GRAFANA İÇİN MOCK ENDPOINTLER ---

# 1. ZAMAN SERİSİ VERİSİ (Grafana Time Series / Line Chart için)
@router.get("/sales-trend")
async def mock_sales_trend():
    """
    Son 30 günün satış grafiğini simüle eder.
    Her yenilemede veriler biraz değişir.
    """
    data = []
    base_date = datetime.now()
    
    # Son 30 gün için veri üret
    for i in range(30):
        date = base_date - timedelta(days=29-i)
        # Random ama mantıklı artış azalışlar
        daily_total = random.randint(1000, 5000) 
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": daily_total,
            "order_count": random.randint(10, 50)
        })
    
    return data

# 2. KATEGORİK VERİ (Grafana Pie Chart / Bar Chart için)
@router.get("/category-distribution")
async def mock_category_dist():
    """
    Ürün kategorilerine göre satış dağılımı.
    """
    categories = ["Elektronik", "Giyim", "Ev & Yaşam", "Spor", "Kitap"]
    data = []
    
    for cat in categories:
        data.append({
            "category": cat,
            "value": random.randint(5000, 25000)
        })
        
    return data

# 3. KPI / GAUGE VERİSİ (Grafana Stat veya Gauge Paneli için)
@router.get("/system-kpi")
async def mock_kpi():
    """
    Anlık sistem durumu ve hedefleri simüle eder.
    """
    return {
        "monthly_revenue_target": 100000,
        "current_revenue": random.randint(60000, 95000),
        "active_users": random.randint(120, 300),
        "server_cpu_usage": random.uniform(10.5, 85.0), # Yüzde olarak
        "ai_token_usage": random.randint(1500, 5000)
    }

# 4. TABLO VERİSİ (Grafana Table Paneli için)
@router.get("/recent-transactions")
async def mock_transactions():
    """
    Son işlemleri tablo olarak göstermek için.
    """
    products = ["iPhone 15", "Samsung TV", "Nike Ayakkabı", "Roman Kitabı", "Kahve Makinesi"]
    statuses = ["Completed", "Pending", "Failed"]
    
    data = []
    for i in range(10):
        data.append({
            "id": 1000 + i,
            "product": random.choice(products),
            "amount": random.choice([199, 599, 1200, 4500, 32000]),
            "status": random.choice(statuses),
            "timestamp": (datetime.now() - timedelta(minutes=i*10)).strftime("%H:%M:%S")
        })
        
    return data