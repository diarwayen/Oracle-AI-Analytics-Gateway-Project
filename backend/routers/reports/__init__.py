from fastapi import APIRouter
from routers.reports import mock, real, setup

router = APIRouter()

router.include_router(mock.router)
router.include_router(real.router)
router.include_router(setup.router)



