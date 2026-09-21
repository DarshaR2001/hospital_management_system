import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.auth import User
from app.models.patient import Patient
from app.models.staff import Doctor, Employee
from app.models.appointment import Appointment
from app.models.emr import (
    MedicalRecord,
    Diagnosis,
    Treatment,
    Prescription,
    PrescriptionItem,
)
from app.models.pharmacy import Medicine
from app.schemas.emr import (
    ConsultationCreate,
    MedicalRecordResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    PrescriptionItemResponse,
    DiagnosisResponse,
    TreatmentResponse,
)

router = APIRouter(prefix="/emr", tags=["Electronic Medical Records"])


def generate_record_number() -> str:
    today_str = date.today().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"MR-{today_str}-{short_suffix}"


def generate_prescription_code() -> str:
    today_str = date.today().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"RX-{today_str}-{short_suffix}"


def format_medical_record(rec: MedicalRecord) -> MedicalRecordResponse:
    patient = rec.patient
    doctor = rec.doctor
    doc_user = doctor.employee.user if (doctor and doctor.employee) else None

    presc_responses = []
    for presc in rec.prescriptions:
        items = []
        for it in presc.items:
            items.append(
                PrescriptionItemResponse(
                    id=it.id,
                    medicine_id=it.medicine_id,
                    dosage=it.dosage,
                    frequency=it.frequency,
                    duration=it.duration,
                    instructions=it.instructions,
                    quantity=it.quantity,
                    medicine_name=it.medicine.name if it.medicine else None,
                    medicine_code=it.medicine.code if it.medicine else None,
                    is_dispensed=it.is_dispensed,
                    created_at=it.created_at,
                )
            )
        presc_responses.append(
            PrescriptionResponse(
                id=presc.id,
                prescription_code=presc.prescription_code,
                patient_id=presc.patient_id,
                doctor_id=presc.doctor_id,
                medical_record_id=presc.medical_record_id,
                status=presc.status,
                notes=presc.notes,
                items=items,
                patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
                doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
                created_at=presc.created_at,
            )
        )

    return MedicalRecordResponse(
        id=rec.id,
        record_number=rec.record_number,
        patient_id=rec.patient_id,
        doctor_id=rec.doctor_id,
        appointment_id=rec.appointment_id,
        record_date=rec.record_date,
        chief_complaint=rec.chief_complaint,
        physical_examination=rec.physical_examination,
        notes=rec.notes,
        patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
        doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
        diagnoses=[DiagnosisResponse.model_validate(d) for d in rec.diagnoses],
        treatments=[TreatmentResponse.model_validate(t) for t in rec.treatments],
        prescriptions=presc_responses,
        created_at=rec.created_at,
    )


@router.post("/consultation", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    payload: ConsultationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR"])),
):
    # Verify patient & doctor
    patient = await db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor = await db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # If appointment provided, mark as completed
    if payload.appointment_id:
        appt = await db.get(Appointment, payload.appointment_id)
        if appt:
            appt.status = "COMPLETED"
            db.add(appt)

    # 1. Create Medical Record
    record = MedicalRecord(
        record_number=generate_record_number(),
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        appointment_id=payload.appointment_id,
        record_date=date.today(),
        chief_complaint=payload.chief_complaint,
        physical_examination=payload.physical_examination,
        notes=payload.notes,
    )
    db.add(record)
    await db.flush()

    # 2. Add Diagnoses
    for diag in payload.diagnoses:
        d = Diagnosis(
            medical_record_id=record.id,
            diagnosis_name=diag.diagnosis_name,
            icd_code=diag.icd_code,
            diagnosis_type=diag.diagnosis_type,
            notes=diag.notes,
        )
        db.add(d)

    # 3. Add Treatments
    for tr in payload.treatments:
        t = Treatment(
            medical_record_id=record.id,
            treatment_name=tr.treatment_name,
            instructions=tr.instructions,
            status=tr.status,
        )
        db.add(t)

    # 4. Add Prescription if items provided
    if payload.prescription_items:
        presc = Prescription(
            prescription_code=generate_prescription_code(),
            medical_record_id=record.id,
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            status="ACTIVE",
            notes=payload.notes,
        )
        db.add(presc)
        await db.flush()

        for item in payload.prescription_items:
            pi = PrescriptionItem(
                prescription_id=presc.id,
                medicine_id=item.medicine_id,
                dosage=item.dosage,
                frequency=item.frequency,
                duration=item.duration,
                instructions=item.instructions,
                quantity=item.quantity,
                is_dispensed=False,
            )
            db.add(pi)

    await db.commit()

    # Reload record with all relationships
    stmt = (
        select(MedicalRecord)
        .where(MedicalRecord.id == record.id)
        .options(
            selectinload(MedicalRecord.patient),
            selectinload(MedicalRecord.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(MedicalRecord.diagnoses),
            selectinload(MedicalRecord.treatments),
            selectinload(MedicalRecord.prescriptions).selectinload(Prescription.items).selectinload(PrescriptionItem.medicine),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_medical_record(loaded)


@router.get("/records", response_model=List[MedicalRecordResponse])
async def list_medical_records(
    patient_id: Optional[uuid.UUID] = None,
    doctor_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(MedicalRecord)
        .options(
            selectinload(MedicalRecord.patient),
            selectinload(MedicalRecord.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(MedicalRecord.diagnoses),
            selectinload(MedicalRecord.treatments),
            selectinload(MedicalRecord.prescriptions).selectinload(Prescription.items).selectinload(PrescriptionItem.medicine),
        )
    )
    if patient_id:
        stmt = stmt.where(MedicalRecord.patient_id == patient_id)
    if doctor_id:
        stmt = stmt.where(MedicalRecord.doctor_id == doctor_id)

    stmt = stmt.order_by(MedicalRecord.record_date.desc(), MedicalRecord.created_at.desc()).offset(offset).limit(limit)
    records = (await db.execute(stmt)).scalars().all()
    return [format_medical_record(r) for r in records]


@router.get("/records/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(MedicalRecord)
        .where(MedicalRecord.id == record_id)
        .options(
            selectinload(MedicalRecord.patient),
            selectinload(MedicalRecord.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(MedicalRecord.diagnoses),
            selectinload(MedicalRecord.treatments),
            selectinload(MedicalRecord.prescriptions).selectinload(Prescription.items).selectinload(PrescriptionItem.medicine),
        )
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return format_medical_record(record)


@router.get("/prescriptions", response_model=List[PrescriptionResponse])
async def list_prescriptions(
    patient_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Prescription)
        .options(
            selectinload(Prescription.patient),
            selectinload(Prescription.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Prescription.items).selectinload(PrescriptionItem.medicine),
        )
    )
    if patient_id:
        stmt = stmt.where(Prescription.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(Prescription.status == status_filter.upper())

    stmt = stmt.order_by(Prescription.created_at.desc())
    prescriptions = (await db.execute(stmt)).scalars().all()

    resp = []
    for presc in prescriptions:
        patient = presc.patient
        doctor = presc.doctor
        doc_user = doctor.employee.user if (doctor and doctor.employee) else None
        items = [
            PrescriptionItemResponse(
                id=it.id,
                medicine_id=it.medicine_id,
                dosage=it.dosage,
                frequency=it.frequency,
                duration=it.duration,
                instructions=it.instructions,
                quantity=it.quantity,
                medicine_name=it.medicine.name if it.medicine else None,
                medicine_code=it.medicine.code if it.medicine else None,
                is_dispensed=it.is_dispensed,
                created_at=it.created_at,
            )
            for it in presc.items
        ]
        resp.append(
            PrescriptionResponse(
                id=presc.id,
                prescription_code=presc.prescription_code,
                patient_id=presc.patient_id,
                doctor_id=presc.doctor_id,
                medical_record_id=presc.medical_record_id,
                status=presc.status,
                notes=presc.notes,
                items=items,
                patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
                doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
                created_at=presc.created_at,
            )
        )
    return resp
