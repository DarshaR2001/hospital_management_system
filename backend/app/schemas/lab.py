import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class LaboratoryTestBase(BaseModel):
    test_code: str
    test_name: str
    category: str
    price: float = 0.0
    normal_range: Optional[str] = None
    units: Optional[str] = None
    is_active: bool = True


class LaboratoryTestCreate(LaboratoryTestBase):
    pass


class LaboratoryTestResponse(LaboratoryTestBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class LabResultInput(BaseModel):
    test_id: uuid.UUID
    result_value: str
    normal_range: Optional[str] = None
    remarks: Optional[str] = None
    status: str = "NORMAL"  # NORMAL, ABNORMAL, CRITICAL


class LabResultResponse(LabResultInput):
    id: uuid.UUID
    request_id: uuid.UUID
    test_name: Optional[str] = None
    test_code: Optional[str] = None
    units: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LabTestRequestCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    test_ids: List[uuid.UUID] = Field(..., min_length=1)
    clinical_notes: Optional[str] = None
    sample_type: Optional[str] = None


class LabTestSampleUpdate(BaseModel):
    sample_type: str


class LabTestRequestResponse(BaseModel):
    id: uuid.UUID
    request_number: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    status: str
    clinical_notes: Optional[str] = None
    sample_type: Optional[str] = None
    sample_collected_at: Optional[datetime] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    results: List[LabResultResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
