import uuid
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field


class AppointmentBase(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    appointment_time: time
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        description="SCHEDULED, CONFIRMED, CHECKED_IN, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW",
    )
    notes: Optional[str] = None


class AppointmentReschedule(BaseModel):
    appointment_date: date
    appointment_time: time
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: uuid.UUID
    appointment_number: str
    status: str
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    patient_phone: Optional[str] = None
    doctor_name: Optional[str] = None
    specialization: Optional[str] = None
    consultation_fee: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
