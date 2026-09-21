import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InvoiceItemInput(BaseModel):
    item_type: str = Field(..., description="CONSULTATION, LAB_TEST, PHARMACY, ADMISSION, OTHER")
    item_description: str
    quantity: int = 1
    unit_price: float
    reference_id: Optional[str] = None


class InvoiceItemResponse(InvoiceItemInput):
    id: uuid.UUID
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="CASH, CARD, UPI, BANK_TRANSFER, INSURANCE")
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentCreate):
    id: uuid.UUID
    invoice_id: uuid.UUID
    payment_number: str
    payment_date: datetime

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    patient_id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    discount: float = 0.0
    tax: float = 0.0
    notes: Optional[str] = None
    items: List[InvoiceItemInput] = Field(..., min_length=1)


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    patient_id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    total_amount: float
    discount: float
    tax: float
    paid_amount: float
    balance_amount: float
    status: str
    notes: Optional[str] = None
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    items: List[InvoiceItemResponse] = []
    payments: List[PaymentResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
