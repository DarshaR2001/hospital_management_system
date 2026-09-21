import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BedResponse(BaseModel):
    id: uuid.UUID
    ward_id: uuid.UUID
    bed_number: str
    status: str
    daily_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class WardBase(BaseModel):
    name: str
    ward_type: str
    floor: Optional[str] = None
    capacity: int = 10
    is_active: bool = True


class WardCreate(WardBase):
    pass


class WardResponse(WardBase):
    id: uuid.UUID
    beds: List[BedResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class AdmissionCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    bed_id: uuid.UUID
    admission_reason: str


class AdmissionTransfer(BaseModel):
    new_bed_id: uuid.UUID
    reason: Optional[str] = None


class AdmissionDischarge(BaseModel):
    discharge_summary: str


class AdmissionResponse(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    bed_id: uuid.UUID
    admission_date: datetime
    discharge_date: Optional[datetime] = None
    admission_reason: str
    discharge_summary: Optional[str] = None
    status: str
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    doctor_name: Optional[str] = None
    bed_number: Optional[str] = None
    ward_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
