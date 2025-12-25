from fastapi import APIRouter, Depends
from core.security import get_api_key
from routers.dashboard import (
    employees,
    education,
    age,
    blood,
    location,
    engagement,
    turnover,
    family,
    interns,
    hr_training,
)

# API key authentication tüm dashboard endpoint'leri için zorunlu
router = APIRouter(dependencies=[Depends(get_api_key)])


router.include_router(employees.router)
router.include_router(education.router)
router.include_router(age.router)
router.include_router(blood.router)
router.include_router(location.router)
router.include_router(engagement.router)
router.include_router(turnover.router)
router.include_router(family.router)
router.include_router(interns.router)
router.include_router(hr_training.router)