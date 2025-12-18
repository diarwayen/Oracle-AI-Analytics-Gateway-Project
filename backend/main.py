from fastapi import FastAPI
from routers import ai, reports  # Router dosyalarımızı çağırdık

app = FastAPI(
    title="Oracle AI Analytics Gateway",
    version="1.0.0"
)

# --- ROUTERLARI BAĞLAMA ---

# 1. AI rotalarını "/api" önekiyle ekle
# Sonuç: /api/ask-ai
app.include_router(ai.router, prefix="/api", tags=["AI Chat"])

# 2. Rapor rotalarını "/reports" önekiyle ekle
# Sonuç: /reports/top-sales
app.include_router(reports.router, prefix="/reports", tags=["Fixed Reports"])

@app.get("/")
def read_root():
    return {"status": "Gateway Calisiyor", "docs": "/docs"}