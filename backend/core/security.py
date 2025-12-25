from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from core.config import settings

API_KEY_NAME = settings.API_KEY_NAME
# auto_error=True: Header yoksa otomatik olarak 403 hatası döner
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    API key doğrulama fonksiyonu.
    Header'da X-API-Key bulunmalı ve geçerli olmalıdır.
    """
    expected_key = settings.ORACLE_GATEWAY_API_KEY

    if not expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key yapılandırılmamış.",
        )

    # auto_error=True olduğu için api_key None olamaz, ama yine de kontrol edelim
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key header eksik.",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Geçersiz API key.",
        )

    return api_key


