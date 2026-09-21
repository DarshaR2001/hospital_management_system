import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.auth import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.emr import MedicalRecord, Prescription
from app.models.lab import LabTestRequest
from app.models.billing import Invoice
from app.models.inpatient import Admission
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientHistoryResponse,
)

router = APIRouter(prefix="/patients", tags=["Patients"])


def generate_patient_code() -> str:
    today_str = date.today().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"PAT-{today_str}-{short_suffix}"


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    q: Optional[str] = Query(None, description="Search by name, phone, or patient code"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Patient)
    if q:
        search = f"%{q}%"
        stmt = stmt.where(
            or_(
                Patient.first_name.ilike(search),
                Patient.last_name.ilike(search),
                Patient.phone.ilike(search),
                Patient.patient_code.ilike(search),
            )
        )
    stmt = stmt.order_by(Patient.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def register_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "RECEPTIONIST", "NURSE", "DOCTOR"])),
):
    patient_code = generate_patient_code()
    patient = Patient(
        patient_code=patient_code,
        **payload.model_dump(),
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "RECEPTIONIST", "NURSE", "DOCTOR"])),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR"])),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    await db.delete(patient)
    await db.commit()
    return {"message": "Patient deleted successfully"}


@router.get("/{patient_id}/history", response_model=PatientHistoryResponse)
async def get_patient_history(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Counts
    appts = (await db.execute(select(func.count(Appointment.id)).where(Appointment.patient_id == patient_id))).scalar() or 0
    records = (await db.execute(select(func.count(MedicalRecord.id)).where(MedicalRecord.patient_id == patient_id))).scalar() or 0
    prescriptions = (await db.execute(select(func.count(Prescription.id)).where(Prescription.patient_id == patient_id))).scalar() or 0
    labs = (await db.execute(select(func.count(LabTestRequest.id)).where(LabTestRequest.patient_id == patient_id))).scalar() or 0
    invoices = (await db.execute(select(func.count(Invoice.id)).where(Invoice.patient_id == patient_id))).scalar() or 0
    admissions = (await db.execute(select(func.count(Admission.id)).where(Admission.patient_id == patient_id))).scalar() or 0

    return PatientHistoryResponse(
        id=patient.id,
        patient_code=patient.patient_code,
        first_name=patient.first_name,
        last_name=patient.last_name,
        gender=patient.gender,
        dob=patient.dob,
        blood_group=patient.blood_group,
        phone=patient.phone,
        email=patient.email,
        address=patient.address,
        emergency_contact=patient.emergency_contact,
        emergency_phone=patient.emergency_phone,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        appointments_count=appts,
        medical_records_count=records,
        prescriptions_count=prescriptions,
        lab_requests_count=labs,
        invoices_count=invoices,
        admissions_count=admissions,
    )
