import uuid
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# Department Schemas
class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    description: Optional[str] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Employee Schemas
class EmployeeBase(BaseModel):
    employee_code: str
    designation: str
    qualification: Optional[str] = None
    joining_date: date
    department_id: Optional[uuid.UUID] = None


class EmployeeCreate(EmployeeBase):
    # If creating user along with employee
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    phone: Optional[str] = None
    role_name: str


class EmployeeUpdate(BaseModel):
    designation: Optional[str] = None
    qualification: Optional[str] = None
    department_id: Optional[uuid.UUID] = None


class EmployeeResponse(EmployeeBase):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Doctor Schedule Schemas
class DoctorScheduleBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    slot_duration_minutes: int = 15
    is_active: bool = True


class DoctorScheduleCreate(DoctorScheduleBase):
    doctor_id: uuid.UUID


class DoctorScheduleResponse(DoctorScheduleBase):
    id: uuid.UUID
    doctor_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Doctor Schemas
class DoctorBase(BaseModel):
    specialization: str
    license_number: str
    consultation_fee: float = 0.0
    room_number: Optional[str] = None


class DoctorCreate(DoctorBase):
    # Option to link existing employee or create doctor with new employee + user
    employee_id: Optional[uuid.UUID] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    qualification: Optional[str] = None


class DoctorUpdate(BaseModel):
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    consultation_fee: Optional[float] = None
    room_number: Optional[str] = None


class DoctorResponse(DoctorBase):
    id: uuid.UUID
    employee_id: uuid.UUID
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    schedules: List[DoctorScheduleResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
