import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MedicineBase(BaseModel):
    code: str
    name: str
    generic_name: Optional[str] = None
    category: str
    dosage_form: str
    unit_price: float = 0.0
    reorder_level: int = 50
    is_active: bool = True


class MedicineCreate(MedicineBase):
    initial_batch_number: Optional[str] = None
    initial_quantity: Optional[int] = None
    expiry_date: Optional[date] = None
    purchase_price: Optional[float] = None


class MedicineBatchCreate(BaseModel):
    medicine_id: uuid.UUID
    batch_number: str
    expiry_date: date
    quantity: int = Field(..., gt=0)
    purchase_price: float = 0.0


class MedicineBatchResponse(BaseModel):
    id: uuid.UUID
    medicine_id: uuid.UUID
    batch_number: str
    expiry_date: date
    quantity: int
    purchase_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class MedicineResponse(MedicineBase):
    id: uuid.UUID
    total_stock: int = 0
    batches: List[MedicineBatchResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class DispenseItemRequest(BaseModel):
    prescription_item_id: uuid.UUID
    batch_id: uuid.UUID
    quantity: int = Field(..., gt=0)


class DispensePrescriptionRequest(BaseModel):
    prescription_id: uuid.UUID
    dispense_items: List[DispenseItemRequest]
