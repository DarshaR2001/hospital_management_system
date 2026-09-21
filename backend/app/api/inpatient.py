import uuid
from datetime import datetime, timezone
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
from app.models.inpatient import Ward, Bed, Admission
from app.schemas.inpatient import (
    WardCreate,
    WardResponse,
    BedResponse,
    AdmissionCreate,
    AdmissionResponse,
    AdmissionTransfer,
    AdmissionDischarge,
)

router = APIRouter(prefix="/inpatient", tags=["Inpatient & Beds"])


def generate_admission_number() -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"ADM-{today_str}-{short_suffix}"


def format_admission_response(adm: Admission) -> AdmissionResponse:
    patient = adm.patient
    doctor = adm.doctor
    bed = adm.bed
    doc_user = doctor.employee.user if (doctor and doctor.employee) else None

    return AdmissionResponse(
        id=adm.id,
        admission_number=adm.admission_number,
        patient_id=adm.patient_id,
        doctor_id=adm.doctor_id,
        bed_id=adm.bed_id,
        admission_date=adm.admission_date,
        discharge_date=adm.discharge_date,
        admission_reason=adm.admission_reason,
        discharge_summary=adm.discharge_summary,
        status=adm.status,
        patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
        patient_code=patient.patient_code if patient else None,
        doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
        bed_number=bed.bed_number if bed else None,
        ward_name=bed.ward.name if (bed and bed.ward) else None,
        created_at=adm.created_at,
    )


# ================= WARDS & BEDS =================

@router.get("/wards", response_model=List[WardResponse])
async def list_wards(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Ward).options(selectinload(Ward.beds)).where(Ward.is_active.is_(True)).order_by(Ward.name)
    result = await db.execute(stmt)
    wards = result.scalars().all()
    resp = []
    for w in wards:
        beds_list = [
            BedResponse(
                id=b.id,
                ward_id=b.ward_id,
                bed_number=b.bed_number,
                status=b.status,
                daily_rate=float(b.daily_rate),
                created_at=b.created_at,
            )
            for b in w.beds
        ]
        resp.append(
            WardResponse(
                id=w.id,
                name=w.name,
                ward_type=w.ward_type,
                floor=w.floor,
                capacity=w.capacity,
                is_active=w.is_active,
                beds=beds_list,
                created_at=w.created_at,
            )
        )
    return resp


@router.post("/wards", response_model=WardResponse, status_code=status.HTTP_201_CREATED)
async def create_ward(
    payload: WardCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR"])),
):
    ward = Ward(**payload.model_dump())
    db.add(ward)
    await db.commit()
    await db.refresh(ward)
    return WardResponse(
        id=ward.id,
        name=ward.name,
        ward_type=ward.ward_type,
        floor=ward.floor,
        capacity=ward.capacity,
        is_active=ward.is_active,
        beds=[],
        created_at=ward.created_at,
    )


@router.get("/beds", response_model=List[BedResponse])
async def list_beds(
    ward_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Bed)
    if ward_id:
        stmt = stmt.where(Bed.ward_id == ward_id)
    if status_filter:
        stmt = stmt.where(Bed.status == status_filter.upper())
    stmt = stmt.order_by(Bed.bed_number)
    result = await db.execute(stmt)
    beds = result.scalars().all()
    return [
        BedResponse(
            id=b.id,
            ward_id=b.ward_id,
            bed_number=b.bed_number,
            status=b.status,
            daily_rate=float(b.daily_rate),
            created_at=b.created_at,
        )
        for b in beds
    ]


# ================= ADMISSIONS WORKFLOW =================

@router.post("/admissions", response_model=AdmissionResponse, status_code=status.HTTP_201_CREATED)
async def admit_patient(
    payload: AdmissionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR", "NURSE"])),
):
    patient = await db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor = await db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    bed = await db.get(Bed, payload.bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")

    if bed.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail=f"Bed {bed.bed_number} is currently {bed.status}")

    # Mark bed as occupied
    bed.status = "OCCUPIED"
    db.add(bed)

    admission = Admission(
        admission_number=generate_admission_number(),
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        bed_id=payload.bed_id,
        admission_date=datetime.now(timezone.utc),
        admission_reason=payload.admission_reason,
        status="ADMITTED",
    )
    db.add(admission)
    await db.commit()

    stmt = (
        select(Admission)
        .where(Admission.id == admission.id)
        .options(
            selectinload(Admission.patient),
            selectinload(Admission.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Admission.bed).selectinload(Bed.ward),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_admission_response(loaded)


@router.get("/admissions", response_model=List[AdmissionResponse])
async def list_admissions(
    status_filter: Optional[str] = Query(None, alias="status"),
    patient_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Admission)
        .options(
            selectinload(Admission.patient),
            selectinload(Admission.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Admission.bed).selectinload(Bed.ward),
        )
    )
    if status_filter:
        stmt = stmt.where(Admission.status == status_filter.upper())
    if patient_id:
        stmt = stmt.where(Admission.patient_id == patient_id)

    stmt = stmt.order_by(Admission.admission_date.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    admissions = result.scalars().all()
    return [format_admission_response(a) for a in admissions]


@router.get("/admissions/{admission_id}", response_model=AdmissionResponse)
async def get_admission(
    admission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Admission)
        .where(Admission.id == admission_id)
        .options(
            selectinload(Admission.patient),
            selectinload(Admission.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Admission.bed).selectinload(Bed.ward),
        )
    )
    adm = (await db.execute(stmt)).scalar_one_or_none()
    if not adm:
        raise HTTPException(status_code=404, detail="Admission not found")
    return format_admission_response(adm)


@router.post("/admissions/{admission_id}/transfer", response_model=AdmissionResponse)
async def transfer_patient(
    admission_id: uuid.UUID,
    payload: AdmissionTransfer,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR", "NURSE"])),
):
    adm = await db.get(Admission, admission_id)
    if not adm or adm.status != "ADMITTED":
        raise HTTPException(status_code=400, detail="Active admission record not found")

    new_bed = await db.get(Bed, payload.new_bed_id)
    if not new_bed or new_bed.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Target bed is not available")

    # Free old bed
    old_bed = await db.get(Bed, adm.bed_id)
    if old_bed:
        old_bed.status = "AVAILABLE"
        db.add(old_bed)

    # Occupy new bed
    new_bed.status = "OCCUPIED"
    db.add(new_bed)

    adm.bed_id = new_bed.id
    if payload.reason:
        adm.admission_reason = f"{adm.admission_reason}\nTransferred: {payload.reason}".strip()

    db.add(adm)
    await db.commit()

    stmt = (
        select(Admission)
        .where(Admission.id == adm.id)
        .options(
            selectinload(Admission.patient),
            selectinload(Admission.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Admission.bed).selectinload(Bed.ward),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_admission_response(loaded)


@router.post("/admissions/{admission_id}/discharge", response_model=AdmissionResponse)
async def discharge_patient(
    admission_id: uuid.UUID,
    payload: AdmissionDischarge,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR", "NURSE"])),
):
    adm = await db.get(Admission, admission_id)
    if not adm or adm.status != "ADMITTED":
        raise HTTPException(status_code=400, detail="Active admission record not found")

    # Free the bed
    bed = await db.get(Bed, adm.bed_id)
    if bed:
        bed.status = "AVAILABLE"
        db.add(bed)

    adm.discharge_date = datetime.now(timezone.utc)
    adm.discharge_summary = payload.discharge_summary
    adm.status = "DISCHARGED"
    db.add(adm)
    await db.commit()

    stmt = (
        select(Admission)
        .where(Admission.id == adm.id)
        .options(
            selectinload(Admission.patient),
            selectinload(Admission.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Admission.bed).selectinload(Bed.ward),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_admission_response(loaded)
