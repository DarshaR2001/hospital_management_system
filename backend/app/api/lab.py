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
from app.models.lab import LaboratoryTest, LabTestRequest, LabResult
from app.schemas.lab import (
    LaboratoryTestCreate,
    LaboratoryTestResponse,
    LabTestRequestCreate,
    LabTestRequestResponse,
    LabTestSampleUpdate,
    LabResultInput,
    LabResultResponse,
)

router = APIRouter(prefix="/lab", tags=["Laboratory"])


def generate_lab_request_number() -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"LAB-{today_str}-{short_suffix}"


def format_lab_request(req: LabTestRequest) -> LabTestRequestResponse:
    patient = req.patient
    doctor = req.doctor
    doc_user = doctor.employee.user if (doctor and doctor.employee) else None

    res_list = []
    for r in req.results:
        test = r.test
        res_list.append(
            LabResultResponse(
                id=r.id,
                request_id=r.request_id,
                test_id=r.test_id,
                result_value=r.result_value,
                normal_range=r.normal_range or (test.normal_range if test else None),
                remarks=r.remarks,
                status=r.status,
                test_name=test.test_name if test else None,
                test_code=test.test_code if test else None,
                units=test.units if test else None,
                verified_at=r.verified_at,
                created_at=r.created_at,
            )
        )

    return LabTestRequestResponse(
        id=req.id,
        request_number=req.request_number,
        patient_id=req.patient_id,
        doctor_id=req.doctor_id,
        appointment_id=req.appointment_id,
        status=req.status,
        clinical_notes=req.clinical_notes,
        sample_type=req.sample_type,
        sample_collected_at=req.sample_collected_at,
        patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
        doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
        results=res_list,
        created_at=req.created_at,
    )


# ================= TESTS CATALOG =================

@router.get("/tests", response_model=List[LaboratoryTestResponse])
async def list_lab_tests(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(LaboratoryTest).where(LaboratoryTest.is_active.is_(True))
    if category:
        stmt = stmt.where(LaboratoryTest.category.ilike(f"%{category}%"))
    stmt = stmt.order_by(LaboratoryTest.test_name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/tests", response_model=LaboratoryTestResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_test(
    payload: LaboratoryTestCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "LAB_STAFF"])),
):
    existing = (
        await db.execute(select(LaboratoryTest).where(LaboratoryTest.test_code == payload.test_code))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Test with this code already exists")

    test = LaboratoryTest(**payload.model_dump())
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return test


# ================= REQUESTS WORKFLOW =================

@router.post("/requests", response_model=LabTestRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_request(
    payload: LabTestRequestCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR"])),
):
    patient = await db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor = await db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    lab_req = LabTestRequest(
        request_number=generate_lab_request_number(),
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        appointment_id=payload.appointment_id,
        status="REQUESTED",
        clinical_notes=payload.clinical_notes,
        sample_type=payload.sample_type,
    )
    db.add(lab_req)
    await db.flush()

    # Pre-create empty results for each test
    for t_id in payload.test_ids:
        test = await db.get(LaboratoryTest, t_id)
        if test:
            res = LabResult(
                request_id=lab_req.id,
                test_id=t_id,
                result_value="PENDING",
                normal_range=test.normal_range,
                status="PENDING",
            )
            db.add(res)

    await db.commit()

    stmt = (
        select(LabTestRequest)
        .where(LabTestRequest.id == lab_req.id)
        .options(
            selectinload(LabTestRequest.patient),
            selectinload(LabTestRequest.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(LabTestRequest.results).selectinload(LabResult.test),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_lab_request(loaded)


@router.get("/requests", response_model=List[LabTestRequestResponse])
async def list_lab_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    patient_id: Optional[uuid.UUID] = None,
    doctor_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(LabTestRequest)
        .options(
            selectinload(LabTestRequest.patient),
            selectinload(LabTestRequest.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(LabTestRequest.results).selectinload(LabResult.test),
        )
    )
    if status_filter:
        stmt = stmt.where(LabTestRequest.status == status_filter.upper())
    if patient_id:
        stmt = stmt.where(LabTestRequest.patient_id == patient_id)
    if doctor_id:
        stmt = stmt.where(LabTestRequest.doctor_id == doctor_id)

    stmt = stmt.order_by(LabTestRequest.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    requests = result.scalars().all()
    return [format_lab_request(r) for r in requests]


@router.get("/requests/{request_id}", response_model=LabTestRequestResponse)
async def get_lab_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(LabTestRequest)
        .where(LabTestRequest.id == request_id)
        .options(
            selectinload(LabTestRequest.patient),
            selectinload(LabTestRequest.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(LabTestRequest.results).selectinload(LabResult.test),
        )
    )
    req = (await db.execute(stmt)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Lab test request not found")
    return format_lab_request(req)


@router.patch("/requests/{request_id}/sample", response_model=LabTestRequestResponse)
async def update_sample_collection(
    request_id: uuid.UUID,
    payload: LabTestSampleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "LAB_STAFF", "NURSE"])),
):
    req = await db.get(LabTestRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Lab test request not found")

    req.sample_type = payload.sample_type
    req.sample_collected_at = datetime.now(timezone.utc)
    req.status = "SAMPLE_COLLECTED"
    db.add(req)
    await db.commit()

    stmt = (
        select(LabTestRequest)
        .where(LabTestRequest.id == request_id)
        .options(
            selectinload(LabTestRequest.patient),
            selectinload(LabTestRequest.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(LabTestRequest.results).selectinload(LabResult.test),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_lab_request(loaded)


@router.post("/requests/{request_id}/results", response_model=LabTestRequestResponse)
async def enter_lab_results(
    request_id: uuid.UUID,
    results_input: List[LabResultInput],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMINISTRATOR", "LAB_STAFF"])),
):
    req = await db.get(LabTestRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Lab test request not found")

    for item in results_input:
        stmt = select(LabResult).where(
            LabResult.request_id == request_id,
            LabResult.test_id == item.test_id,
        )
        existing_res = (await db.execute(stmt)).scalar_one_or_none()
        if existing_res:
            existing_res.result_value = item.result_value
            existing_res.remarks = item.remarks
            existing_res.status = item.status.upper()
            existing_res.performed_by_id = current_user.id
            existing_res.verified_at = datetime.now(timezone.utc)
            if item.normal_range:
                existing_res.normal_range = item.normal_range
            db.add(existing_res)
        else:
            new_res = LabResult(
                request_id=request_id,
                test_id=item.test_id,
                result_value=item.result_value,
                normal_range=item.normal_range,
                remarks=item.remarks,
                status=item.status.upper(),
                performed_by_id=current_user.id,
                verified_at=datetime.now(timezone.utc),
            )
            db.add(new_res)

    req.status = "COMPLETED"
    db.add(req)
    await db.commit()

    stmt = (
        select(LabTestRequest)
        .where(LabTestRequest.id == request_id)
        .options(
            selectinload(LabTestRequest.patient),
            selectinload(LabTestRequest.doctor).selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(LabTestRequest.results).selectinload(LabResult.test),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_lab_request(loaded)
