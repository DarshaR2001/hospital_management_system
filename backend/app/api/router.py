from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.staff import router as staff_router
from app.api.patients import router as patients_router
from app.api.appointments import router as appointments_router
from app.api.emr import router as emr_router
from app.api.lab import router as lab_router
from app.api.pharmacy import router as pharmacy_router
from app.api.billing import router as billing_router
from app.api.inpatient import router as inpatient_router
from app.api.reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(staff_router)
api_router.include_router(patients_router)
api_router.include_router(appointments_router)
api_router.include_router(emr_router)
api_router.include_router(lab_router)
api_router.include_router(pharmacy_router)
api_router.include_router(billing_router)
api_router.include_router(inpatient_router)
api_router.include_router(reports_router)
