from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette import status


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status": exc.status_code},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        # Gizli detayları sızdırmamak için genel mesaj
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Beklenmeyen hata", "status": 500},
        )

