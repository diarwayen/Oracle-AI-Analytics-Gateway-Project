from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import ai
from routers import reports
from core.errors import register_exception_handlers
from services.oracle import init_pool, close_pool

# --- LIFESPAN: Uygulama Başlangıç/Bitiş Yönetimi ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Havuzu Başlat
    init_pool()
    yield
    # 2. Shutdown: Havuzu Temizle
    close_pool()

app = FastAPI(
    title="Oracle AI Analytics Gateway",
    version="1.0.0",
    lifespan=lifespan  # Lifespan'i buraya bağlıyoruz
)

app.include_router(ai.router, prefix="/api", tags=["AI Chat"])
app.include_router(reports.router, prefix="/reports", tags=["Fixed Reports"])

register_exception_handlers(app)

@app.get("/")
def read_root():
    return {"status": "Gateway Calisiyor", "docs": "/docs"}