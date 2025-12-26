from fastapi import APIRouter, Depends
from core.security import get_api_key
from routers.ai import live

router = APIRouter(dependencies=[Depends(get_api_key)])

router.include_router(live.router)

