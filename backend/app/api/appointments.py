import uuid
from datetime import date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.auth import User
from app.models.patient import Patient
from app.models.staff import Doctor, Employee
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    AppointmentReschedule,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])

VALID_STATUSES = {
    "SCHEDULED",
    "CONFIRMED",
    "CHECKED_IN",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    "NO_SHOW",
}


def generate_appointment_number() -> str:
    today_str = date.today().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"APT-{today_str}-{short_suffix}"


def format_appointment_response(appt: Appointment) -> AppointmentResponse:
    patient = appt.patient
    doctor = appt.doctor
    doc_user = doctor.employee.user if (doctor and doctor.employee) else None

    return AppointmentResponse(
        id=appt.id,
        appointment_number=appt.appointment_number,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        appointment_date=appt.appointment_date,
        appointment_time=appt.appointment_time,
        status=appt.status,
        reason=appt.reason,
        notes=appt.notes,
        patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
        patient_code=patient.patient_code if patient else None,
        patient_phone=patient.phone if patient else None,
        doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
        specialization=doctor.specialization if doctor else None,
        consultation_fee=float(doctor.consultation_fee) if doctor else 0.0,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
    )


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    appointment_date: Optional[date] = None,
    doctor_id: Optional[uuid.UUID] = None,
    patient_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
        )
    )
    if appointment_date:
        stmt = stmt.where(Appointment.appointment_date == appointment_date)
    if doctor_id:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter.upper())

    stmt = stmt.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    appointments = result.scalars().all()

    return [format_appointment_response(appt) for appt in appointments]


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "RECEPTIONIST", "DOCTOR", "NURSE"])),
):
    # Verify patient exists
    patient = await db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Verify doctor exists
    doctor_stmt = (
        select(Doctor)
        .where(Doctor.id == payload.doctor_id)
        .options(selectinload(Doctor.employee).selectinload(Employee.user))
    )
    doctor = (await db.execute(doctor_stmt)).scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Check for doctor double-booking at identical slot
    existing_stmt = select(Appointment).where(
        and_(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.appointment_date == payload.appointment_date,
            Appointment.appointment_time == payload.appointment_time,
            Appointment.status.notin_(["CANCELLED", "NO_SHOW"]),
        )
    )
    existing_appt = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing_appt:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Doctor is already booked at {payload.appointment_time} on {payload.appointment_date}",
        )

    appt = Appointment(
        appointment_number=generate_appointment_number(),
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time,
        status="SCHEDULED",
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(appt)
    await db.commit()

    # Re-fetch with relations
    reload_stmt = (
        select(Appointment)
        .where(Appointment.id == appt.id)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
        )
    )
    loaded = (await db.execute(reload_stmt)).scalar_one()
    return format_appointment_response(loaded)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
        )
    )
    appt = (await db.execute(stmt)).scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return format_appointment_response(appt)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "RECEPTIONIST", "DOCTOR", "NURSE"])),
):
    status_upper = payload.status.upper()
    if status_upper not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")

    stmt = (
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
        )
    )
    appt = (await db.execute(stmt)).scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = status_upper
    if payload.notes:
        appt.notes = f"{appt.notes or ''}\nStatus update: {payload.notes}".strip()

    db.add(appt)
    await db.commit()

    reloaded = (await db.execute(stmt)).scalar_one()
    return format_appointment_response(reloaded)


@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentReschedule,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "RECEPTIONIST", "DOCTOR"])),
):
    stmt = (
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
        )
    )
    appt = (await db.execute(stmt)).scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check for conflict
    existing_stmt = select(Appointment).where(
        and_(
            Appointment.doctor_id == appt.doctor_id,
            Appointment.appointment_date == payload.appointment_date,
            Appointment.appointment_time == payload.appointment_time,
            Appointment.id != appt.id,
            Appointment.status.notin_(["CANCELLED", "NO_SHOW"]),
        )
    )
    conflict = (await db.execute(existing_stmt)).scalar_one_or_none()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Doctor is already booked at {payload.appointment_time} on {payload.appointment_date}",
        )

    appt.appointment_date = payload.appointment_date
    appt.appointment_time = payload.appointment_time
    appt.status = "SCHEDULED"
    if payload.notes:
        appt.notes = f"{appt.notes or ''}\nRescheduled: {payload.notes}".strip()

    db.add(appt)
    await db.commit()

    reloaded = (await db.execute(stmt)).scalar_one()
    return format_appointment_response(reloaded)
