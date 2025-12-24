from fastapi import FastAPI
from routers import ai
from routers import reports
from core.errors import register_exception_handlers

app = FastAPI(
    title="Oracle AI Analytics Gateway",
    version="1.0.0"
)

app.include_router(ai.router, prefix="/api", tags=["AI Chat"])
app.include_router(reports.router, prefix="/reports", tags=["Fixed Reports"])


register_exception_handlers(app)

@app.get("/")
def read_root():
    return {"status": "Gateway Calisiyor", "docs": "/docs"}