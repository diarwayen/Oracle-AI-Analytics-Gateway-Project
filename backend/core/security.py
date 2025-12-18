import os
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED


API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Basit API key doğrulama.
    - Ortam değişkeni: ORACLE_GATEWAY_API_KEY
    - İstek header'ı: X-API-Key
    """
    expected_key = os.getenv("ORACLE_GATEWAY_API_KEY")


    if not expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key yapılandırılmamış.",
        )

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik API key.",
        )

    return api_key


