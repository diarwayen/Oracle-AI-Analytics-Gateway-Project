from fastapi import FastAPI
from routers import ai
from routers import reports

app = FastAPI(
    title="Oracle AI Analytics Gateway",
    version="1.0.0"
)


app.include_router(ai.router, prefix="/api", tags=["AI Chat"])


app.include_router(reports.router, prefix="/reports", tags=["Fixed Reports"])

@app.get("/")
def read_root():
    return {"status": "Gateway Calisiyor", "docs": "/docs"}