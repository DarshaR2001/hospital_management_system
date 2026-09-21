import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DiagnosisInput(BaseModel):
    diagnosis_name: str
    icd_code: Optional[str] = None
    diagnosis_type: str = "PRIMARY"  # PRIMARY, SECONDARY, PROVISIONAL
    notes: Optional[str] = None


class DiagnosisResponse(DiagnosisInput):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TreatmentInput(BaseModel):
    treatment_name: str
    instructions: Optional[str] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED


class TreatmentResponse(TreatmentInput):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PrescriptionItemInput(BaseModel):
    medicine_id: uuid.UUID
    dosage: str  # e.g., "500mg"
    frequency: str  # e.g., "1-0-1"
    duration: str  # e.g., "5 days"
    instructions: Optional[str] = None
    quantity: int = 1


class PrescriptionItemResponse(PrescriptionItemInput):
    id: uuid.UUID
    medicine_name: Optional[str] = None
    medicine_code: Optional[str] = None
    is_dispensed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PrescriptionCreate(BaseModel):
    medical_record_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    notes: Optional[str] = None
    items: List[PrescriptionItemInput] = []


class PrescriptionResponse(BaseModel):
    id: uuid.UUID
    prescription_code: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    medical_record_id: uuid.UUID
    status: str
    notes: Optional[str] = None
    items: List[PrescriptionItemResponse] = []
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConsultationCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    chief_complaint: str
    physical_examination: Optional[str] = None
    notes: Optional[str] = None
    diagnoses: List[DiagnosisInput] = []
    treatments: List[TreatmentInput] = []
    prescription_items: List[PrescriptionItemInput] = []


class MedicalRecordResponse(BaseModel):
    id: uuid.UUID
    record_number: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    record_date: date
    chief_complaint: str
    physical_examination: Optional[str] = None
    notes: Optional[str] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    diagnoses: List[DiagnosisResponse] = []
    treatments: List[TreatmentResponse] = []
    prescriptions: List[PrescriptionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
