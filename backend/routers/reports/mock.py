from fastapi import APIRouter
import random
from datetime import datetime, timedelta

router = APIRouter(tags=["Reports Mock"])


@router.get("/sales-trend")
async def mock_sales_trend():
    data = []
    base_date = datetime.now()
    for i in range(30):
        date = base_date - timedelta(days=29 - i)
        daily_total = random.randint(1000, 5000)
        data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "amount": daily_total,
                "order_count": random.randint(10, 50),
            }
        )
    return data


@router.get("/category-distribution")
async def mock_category_dist():
    categories = ["Elektronik", "Giyim", "Ev & Yaşam", "Spor", "Kitap"]
    data = []
    for cat in categories:
        data.append({"category": cat, "value": random.randint(5000, 25000)})
    return data


@router.get("/system-kpi")
async def mock_kpi():
    return {
        "monthly_revenue_target": 100000,
        "current_revenue": random.randint(60000, 95000),
        "active_users": random.randint(120, 300),
        "server_cpu_usage": random.uniform(10.5, 85.0),
        "ai_token_usage": random.randint(1500, 5000),
    }


@router.get("/recent-transactions")
async def mock_transactions():
    products = ["iPhone 15", "Samsung TV", "Nike Ayakkabı", "Roman Kitabı", "Kahve Makinesi"]
    statuses = ["Completed", "Pending", "Failed"]
    data = []
    for i in range(10):
        data.append(
            {
                "id": 1000 + i,
                "product": random.choice(products),
                "amount": random.choice([199, 599, 1200, 4500, 32000]),
                "status": random.choice(statuses),
                "timestamp": (datetime.now() - timedelta(minutes=i * 10)).strftime("%H:%M:%S"),
            }
        )
    return data

