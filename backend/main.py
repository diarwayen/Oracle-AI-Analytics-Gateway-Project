from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import ai
from routers import dashboard
from core.errors import register_exception_handlers
from services.oracle import init_pool, close_pool
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

# --- LIFESPAN: Uygulama Başlangıç/Bitiş Yönetimi ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Oracle Havuzunu Başlat
    init_pool()
    
    # 2. Redis Cache'i Başlat
    # Docker içinde Redis servis adı 'redis' olduğu için host='redis'
    try:
        # decode_responses=False: Redis'ten bytes döndürmeli
        # fastapi-cache2'nin RedisBackend'i kendi encode/decode işlemini yapar
        # Bu sayede cache'den dönen değer her zaman bytes olur ve coder.decode() güvenli çalışır
        redis = aioredis.from_url("redis://redis:6379", encoding="utf8", decode_responses=False)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        print("Redis Cache Başlatıldı.")
    except Exception as e:
        print(f"Redis başlatılamadı: {e}")

    yield
    
    # 3. Kapanış İşlemleri
    close_pool()

app = FastAPI(
    title="Oracle AI Analytics Gateway",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ai.router, prefix="/api", tags=["AI Chat"])
app.include_router(dashboard.router, prefix="/reports", tags=["Fixed Reports"])

register_exception_handlers(app)

@app.get("/")
def read_root():
    return {"status": "Gateway Calisiyor", "docs": "/docs"}