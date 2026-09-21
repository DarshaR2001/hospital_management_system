import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class PatientBase(BaseModel):
    first_name: str = Field(..., max_length=60)
    last_name: str = Field(..., max_length=60)
    gender: str = Field(..., description="MALE, FEMALE, OTHER")
    dob: date
    blood_group: Optional[str] = None
    phone: str = Field(..., max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientResponse(PatientBase):
    id: uuid.UUID
    patient_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientHistoryResponse(PatientResponse):
    appointments_count: int = 0
    medical_records_count: int = 0
    prescriptions_count: int = 0
    lab_requests_count: int = 0
    invoices_count: int = 0
    admissions_count: int = 0
