from fastapi import APIRouter
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
    real,
)

router = APIRouter()

# yeni router gelirse buraya ekle
router.include_router(real.router) # bunu kaldıracağız. unutma.

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