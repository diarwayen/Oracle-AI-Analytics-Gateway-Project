from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta
from services.oracle import OracleService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ==========================================
# BÖLÜM 1: MOCK DATA (SAHTE VERİLER)
# ==========================================

@router.get("/sales-trend")
async def mock_sales_trend():
    """MOCK: Son 30 günün satış grafiğini simüle eder."""
    data = []
    base_date = datetime.now()
    for i in range(30):
        date = base_date - timedelta(days=29-i)
        daily_total = random.randint(1000, 5000) 
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": daily_total,
            "order_count": random.randint(10, 50)
        })
    return data

@router.get("/category-distribution")
async def mock_category_dist():
    """MOCK: Kategori dağılımı."""
    categories = ["Elektronik", "Giyim", "Ev & Yaşam", "Spor", "Kitap"]
    data = []
    for cat in categories:
        data.append({
            "category": cat,
            "value": random.randint(5000, 25000)
        })
    return data

@router.get("/system-kpi")
async def mock_kpi():
    """MOCK: KPI verileri."""
    return {
        "monthly_revenue_target": 100000,
        "current_revenue": random.randint(60000, 95000),
        "active_users": random.randint(120, 300),
        "server_cpu_usage": random.uniform(10.5, 85.0),
        "ai_token_usage": random.randint(1500, 5000)
    }

@router.get("/recent-transactions")
async def mock_transactions():
    """MOCK: Son işlemler."""
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


# ==========================================
# BÖLÜM 2: REAL DATA (ORACLE VERİTABANI)
# ==========================================

def execute_sql_report(query: str, params: dict = None):
    oracle = OracleService()
    try:
        oracle.connect()
        # Not: params opsiyoneldir
        result = oracle.execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"DB Rapor Hatası: {str(e)}")
        # Kullanıcıya hatayı gösterelim
        return {"error": str(e), "detail": "Lütfen /reports/setup-db adresine giderek tabloları oluşturun."}
    finally:
        oracle.close()

@router.get("/db-sales-trend")
async def real_sales_trend():
    sql = """
    SELECT 
        TO_CHAR(satis_tarihi, 'YYYY-MM-DD') as "date",
        SUM(toplam_tutar) as "amount",
        COUNT(*) as "order_count"
    FROM satislar
    GROUP BY TO_CHAR(satis_tarihi, 'YYYY-MM-DD')
    ORDER BY 1
    """
    return execute_sql_report(sql)

@router.get("/db-category-distribution")
async def real_category_dist():
    sql = """
    SELECT 
        u.kategori as "category",
        SUM(s.toplam_tutar) as "value"
    FROM satislar s
    JOIN urunler u ON s.urun_id = u.id
    GROUP BY u.kategori
    ORDER BY 2 DESC
    """
    return execute_sql_report(sql)

@router.get("/db-kpi")
async def real_kpi():
    oracle = OracleService()
    kpi_data = {}
    try:
        oracle.connect()
        
        # Hata yönetimi için try-except blokları
        try:
            res1 = oracle.execute_query("SELECT SUM(toplam_tutar) as VAL FROM satislar")
            kpi_data["current_revenue"] = res1[0]["VAL"] if isinstance(res1, list) and res1 and res1[0]["VAL"] else 0
        except: kpi_data["current_revenue"] = 0

        try:
            res2 = oracle.execute_query("SELECT COUNT(*) as VAL FROM satislar")
            kpi_data["active_users"] = res2[0]["VAL"] if isinstance(res2, list) and res2 else 0
        except: kpi_data["active_users"] = 0

        try:
            res3 = oracle.execute_query("SELECT COUNT(*) as VAL FROM urunler")
            kpi_data["ai_token_usage"] = res3[0]["VAL"] if isinstance(res3, list) and res3 else 0
        except: kpi_data["ai_token_usage"] = 0

        kpi_data["monthly_revenue_target"] = 100000 
        
    except Exception as e:
        logger.error(f"KPI DB Hatası: {e}")
        return {"error": str(e)}
    finally:
        oracle.close()
        
    return kpi_data

@router.get("/db-transactions")
async def real_transactions():
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
    return execute_sql_report(sql)

# ==========================================
# BÖLÜM 3: ACİL DURUM SETUP (TABLO OLUŞTURUCU)
# ==========================================
@router.get("/setup-db")
async def setup_database():
    """
    Eğer tablolar yoksa oluşturur ve test verisi basar.
    Docker volume sorunlarını çözmek için manuel tetikleyici.
    """
    oracle = OracleService()
    logs = []
    
    commands = [
        # Tabloları temizle (Varsa)
        "BEGIN EXECUTE IMMEDIATE 'DROP TABLE satislar'; EXCEPTION WHEN OTHERS THEN NULL; END;",
        "BEGIN EXECUTE IMMEDIATE 'DROP TABLE urunler'; EXCEPTION WHEN OTHERS THEN NULL; END;",
        
        # Tabloları Oluştur
        """
        CREATE TABLE urunler (
            id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            kategori VARCHAR2(50),
            urun_adi VARCHAR2(100),
            fiyat NUMBER(10, 2),
            stok_miktari NUMBER
        )
        """,
        """
        CREATE TABLE satislar (
            id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            urun_id NUMBER,
            adet NUMBER,
            toplam_tutar NUMBER(10, 2),
            satis_tarihi DATE DEFAULT SYSDATE,
            musteri_sehir VARCHAR2(50),
            CONSTRAINT fk_urun FOREIGN KEY (urun_id) REFERENCES urunler(id)
        )
        """,
        # Veri Ekle - Ürünler
        "INSERT INTO urunler (kategori, urun_adi, fiyat, stok_miktari) VALUES ('Elektronik', 'Laptop Pro 15', 35000, 50)",
        "INSERT INTO urunler (kategori, urun_adi, fiyat, stok_miktari) VALUES ('Elektronik', 'Kablosuz Mouse', 750, 200)",
        "INSERT INTO urunler (kategori, urun_adi, fiyat, stok_miktari) VALUES ('Giyim', 'Kot Pantolon', 1200, 150)",
        "INSERT INTO urunler (kategori, urun_adi, fiyat, stok_miktari) VALUES ('Ev', 'Kahve Makinesi', 4500, 30)",
        "INSERT INTO urunler (kategori, urun_adi, fiyat, stok_miktari) VALUES ('Spor', 'Yoga Matı', 300, 100)",
        
        # Veri Ekle - Satışlar
        "INSERT INTO satislar (urun_id, adet, toplam_tutar, satis_tarihi, musteri_sehir) VALUES (1, 1, 35000, SYSDATE - 1, 'Istanbul')",
        "INSERT INTO satislar (urun_id, adet, toplam_tutar, satis_tarihi, musteri_sehir) VALUES (2, 2, 1500, SYSDATE - 1, 'Ankara')",
        "INSERT INTO satislar (urun_id, adet, toplam_tutar, satis_tarihi, musteri_sehir) VALUES (4, 1, 4500, SYSDATE - 5, 'Izmir')",
        "INSERT INTO satislar (urun_id, adet, toplam_tutar, satis_tarihi, musteri_sehir) VALUES (3, 3, 3600, SYSDATE - 10, 'Bursa')"
    ]
    
    try:
        oracle.connect()
        for sql in commands:
            # PL/SQL blokları commit gerektirmez ama DML gerektirir
            # Bizim execute_query metodumuz otomatik commit yapıyor (INSERT ise)
            # CREATE gibi DDL komutları zaten auto-commit'tir.
            try:
                oracle.execute_query(sql)
                logs.append(f"Başarılı: {sql[:30]}...")
            except Exception as e:
                logs.append(f"Hata ({sql[:10]}...): {str(e)}")
        
        return {"status": "Setup Tamamlandı", "logs": logs}
        
    except Exception as e:
        return {"status": "Genel Hata", "error": str(e)}
    finally:
        oracle.close()