from fastapi import APIRouter
from routers.reports import mock, real, setup

router = APIRouter()

# yeni router gelirse buraya ekle
router.include_router(real.router)