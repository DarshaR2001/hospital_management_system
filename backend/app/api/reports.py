from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.auth import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.inpatient import Admission, Bed
from app.models.lab import LabTestRequest
from app.models.pharmacy import Medicine
from app.models.billing import Invoice, Payment

router = APIRouter(prefix="/reports", tags=["Reports & Dashboard"])


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    today = date.today()

    # Total patients
    total_patients = (await db.execute(select(func.count(Patient.id)))).scalar() or 0

    # Today's appointments
    today_appts = (
        await db.execute(select(func.count(Appointment.id)).where(Appointment.appointment_date == today))
    ).scalar() or 0

    # Completed appointments today
    completed_today_appts = (
        await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.appointment_date == today,
                Appointment.status == "COMPLETED",
            )
        )
    ).scalar() or 0

    # Current Inpatients (Admitted)
    active_admissions = (
        await db.execute(select(func.count(Admission.id)).where(Admission.status == "ADMITTED"))
    ).scalar() or 0

    # Available vs Occupied Beds
    total_beds = (await db.execute(select(func.count(Bed.id)))).scalar() or 0
    available_beds = (
        await db.execute(select(func.count(Bed.id)).where(Bed.status == "AVAILABLE"))
    ).scalar() or 0

    # Pending Lab Requests
    pending_labs = (
        await db.execute(
            select(func.count(LabTestRequest.id)).where(
                LabTestRequest.status.in_(["REQUESTED", "SAMPLE_COLLECTED", "IN_PROGRESS"])
            )
        )
    ).scalar() or 0

    # Low Stock Medicines
    meds = (await db.execute(select(Medicine).options(selectinload(Medicine.batches)))).scalars().all()
    low_stock_count = sum(1 for m in meds if sum(b.quantity for b in m.batches) <= m.reorder_level)

    # Financials
    total_billed = (await db.execute(select(func.coalesce(func.sum(Invoice.total_amount), 0.0)))).scalar() or 0.0
    total_collected = (await db.execute(select(func.coalesce(func.sum(Invoice.paid_amount), 0.0)))).scalar() or 0.0
    total_outstanding = (
        await db.execute(
            select(func.coalesce(func.sum(Invoice.balance_amount), 0.0)).where(
                Invoice.status.in_(["PENDING", "PARTIAL"])
            )
        )
    ).scalar() or 0.0

    return {
        "patients": {
            "total": total_patients,
        },
        "appointments": {
            "today_total": today_appts,
            "today_completed": completed_today_appts,
        },
        "inpatient": {
            "active_admissions": active_admissions,
            "total_beds": total_beds,
            "available_beds": available_beds,
            "occupied_beds": total_beds - available_beds,
        },
        "laboratory": {
            "pending_tests": pending_labs,
        },
        "pharmacy": {
            "low_stock_medicines": low_stock_count,
            "total_medicines": len(meds),
        },
        "financials": {
            "total_billed": float(total_billed),
            "total_collected": float(total_collected),
            "total_outstanding": float(total_outstanding),
        },
    }
