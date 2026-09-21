import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.core.security import get_password_hash
from app.models.auth import User, Role
from app.models.staff import Department, Employee, Doctor, DoctorSchedule
from app.schemas.staff import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    DoctorScheduleCreate,
    DoctorScheduleResponse,
)

router = APIRouter(tags=["Staff & Departments"])


# ================= DEPARTMENTS =================

@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Department)
    if active_only:
        stmt = stmt.where(Department.is_active.is_(True))
    stmt = stmt.order_by(Department.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR"])),
):
    stmt = select(Department).where((Department.name == payload.name) | (Department.code == payload.code))
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Department with this name or code already exists")

    dept = Department(**payload.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    dept = await db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR"])),
):
    dept = await db.get(Department, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dept, key, value)

    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


# ================= EMPLOYEES =================

@router.get("/employees", response_model=List[EmployeeResponse])
async def list_employees(
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Employee).options(selectinload(Employee.user), selectinload(Employee.department))
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    result = await db.execute(stmt)
    employees = result.scalars().all()

    resp = []
    for emp in employees:
        resp.append(
            EmployeeResponse(
                id=emp.id,
                user_id=emp.user_id,
                employee_code=emp.employee_code,
                designation=emp.designation,
                qualification=emp.qualification,
                joining_date=emp.joining_date,
                department_id=emp.department_id,
                full_name=emp.user.full_name if emp.user else None,
                email=emp.user.email if emp.user else None,
                phone=emp.user.phone if emp.user else None,
                department_name=emp.department.name if emp.department else None,
                created_at=emp.created_at,
            )
        )
    return resp


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR"])),
):
    # Check if user already exists
    user_stmt = select(User).where(User.email == payload.email)
    existing_user = (await db.execute(user_stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Find role
    role_stmt = select(Role).where(Role.name == payload.role_name.upper())
    role = (await db.execute(role_stmt)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{payload.role_name}' does not exist")

    # Create user
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create employee
    emp = Employee(
        user_id=user.id,
        department_id=payload.department_id,
        employee_code=payload.employee_code,
        designation=payload.designation,
        qualification=payload.qualification,
        joining_date=payload.joining_date,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    dept_name = None
    if emp.department_id:
        dept = await db.get(Department, emp.department_id)
        if dept:
            dept_name = dept.name

    return EmployeeResponse(
        id=emp.id,
        user_id=emp.user_id,
        employee_code=emp.employee_code,
        designation=emp.designation,
        qualification=emp.qualification,
        joining_date=emp.joining_date,
        department_id=emp.department_id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        department_name=dept_name,
        created_at=emp.created_at,
    )


# ================= DOCTORS =================

@router.get("/doctors", response_model=List[DoctorResponse])
async def list_doctors(
    specialization: Optional[str] = None,
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Doctor)
        .options(
            selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Doctor.employee).selectinload(Employee.department),
            selectinload(Doctor.schedules),
        )
    )
    if specialization:
        stmt = stmt.where(Doctor.specialization.ilike(f"%{specialization}%"))
    if department_id:
        stmt = stmt.join(Employee).where(Employee.department_id == department_id)

    result = await db.execute(stmt)
    doctors = result.scalars().all()

    resp = []
    for doc in doctors:
        doc_user = doc.employee.user if doc.employee else None
        doc_dept = doc.employee.department if doc.employee else None
        resp.append(
            DoctorResponse(
                id=doc.id,
                employee_id=doc.employee_id,
                specialization=doc.specialization,
                license_number=doc.license_number,
                consultation_fee=float(doc.consultation_fee),
                room_number=doc.room_number,
                doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
                department_name=doc_dept.name if doc_dept else None,
                email=doc_user.email if doc_user else None,
                phone=doc_user.phone if doc_user else None,
                schedules=[DoctorScheduleResponse.model_validate(s) for s in doc.schedules if s.is_active],
                created_at=doc.created_at,
            )
        )
    return resp


@router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR"])),
):
    # Check license number uniqueness
    lic_stmt = select(Doctor).where(Doctor.license_number == payload.license_number)
    if (await db.execute(lic_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Doctor with this license number already exists")

    emp_id = payload.employee_id
    doc_user = None
    doc_dept = None

    if not emp_id:
        if not payload.email or not payload.password or not payload.full_name:
            raise HTTPException(status_code=400, detail="Provide employee_id or email, password, and full_name to create doctor")

        role_stmt = select(Role).where(Role.name == "DOCTOR")
        role = (await db.execute(role_stmt)).scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail="DOCTOR role not found in database")

        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            role_id=role.id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        emp_code = f"DOC-{uuid.uuid4().hex[:6].upper()}"
        emp = Employee(
            user_id=user.id,
            department_id=payload.department_id,
            employee_code=emp_code,
            designation=f"Consultant - {payload.specialization}",
            qualification=payload.qualification or "MBBS, MD",
            joining_date=date.today(),
        )
        db.add(emp)
        await db.flush()
        emp_id = emp.id
        doc_user = user
        if payload.department_id:
            doc_dept = await db.get(Department, payload.department_id)

    doc = Doctor(
        employee_id=emp_id,
        specialization=payload.specialization,
        license_number=payload.license_number,
        consultation_fee=payload.consultation_fee,
        room_number=payload.room_number,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    if not doc_user:
        emp = await db.get(Employee, emp_id)
        if emp:
            doc_user = await db.get(User, emp.user_id)
            if emp.department_id:
                doc_dept = await db.get(Department, emp.department_id)

    return DoctorResponse(
        id=doc.id,
        employee_id=doc.employee_id,
        specialization=doc.specialization,
        license_number=doc.license_number,
        consultation_fee=float(doc.consultation_fee),
        room_number=doc.room_number,
        doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
        department_name=doc_dept.name if doc_dept else None,
        email=doc_user.email if doc_user else None,
        phone=doc_user.phone if doc_user else None,
        schedules=[],
        created_at=doc.created_at,
    )


@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Doctor)
        .where(Doctor.id == doctor_id)
        .options(
            selectinload(Doctor.employee).selectinload(Employee.user),
            selectinload(Doctor.employee).selectinload(Employee.department),
            selectinload(Doctor.schedules),
        )
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doc_user = doc.employee.user if doc.employee else None
    doc_dept = doc.employee.department if doc.employee else None
    return DoctorResponse(
        id=doc.id,
        employee_id=doc.employee_id,
        specialization=doc.specialization,
        license_number=doc.license_number,
        consultation_fee=float(doc.consultation_fee),
        room_number=doc.room_number,
        doctor_name=f"Dr. {doc_user.full_name}" if doc_user else None,
        department_name=doc_dept.name if doc_dept else None,
        email=doc_user.email if doc_user else None,
        phone=doc_user.phone if doc_user else None,
        schedules=[DoctorScheduleResponse.model_validate(s) for s in doc.schedules if s.is_active],
        created_at=doc.created_at,
    )


# ================= DOCTOR SCHEDULES =================

@router.get("/doctor-schedules", response_model=List[DoctorScheduleResponse])
async def list_doctor_schedules(
    doctor_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(DoctorSchedule).where(DoctorSchedule.is_active.is_(True))
    if doctor_id:
        stmt = stmt.where(DoctorSchedule.doctor_id == doctor_id)
    stmt = stmt.order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/doctor-schedules", response_model=DoctorScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_schedule(
    payload: DoctorScheduleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR"])),
):
    doc = await db.get(Doctor, payload.doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    schedule = DoctorSchedule(**payload.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/doctor-schedules/{schedule_id}")
async def delete_doctor_schedule(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "DOCTOR"])),
):
    schedule = await db.get(DoctorSchedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
    await db.commit()
    return {"message": "Doctor schedule deleted successfully"}
