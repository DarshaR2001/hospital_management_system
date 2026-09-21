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
from app.models.billing import Invoice, InvoiceItem, Payment
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceItemResponse,
    PaymentCreate,
    PaymentResponse,
)

router = APIRouter(prefix="/billing", tags=["Billing & Payments"])


def generate_invoice_number() -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"INV-{today_str}-{short_suffix}"


def generate_payment_number() -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    short_suffix = uuid.uuid4().hex[:4].upper()
    return f"PAY-{today_str}-{short_suffix}"


def format_invoice_response(inv: Invoice) -> InvoiceResponse:
    patient = inv.patient
    return InvoiceResponse(
        id=inv.id,
        invoice_number=inv.invoice_number,
        patient_id=inv.patient_id,
        appointment_id=inv.appointment_id,
        total_amount=float(inv.total_amount),
        discount=float(inv.discount),
        tax=float(inv.tax),
        paid_amount=float(inv.paid_amount),
        balance_amount=float(inv.balance_amount),
        status=inv.status,
        notes=inv.notes,
        patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
        patient_code=patient.patient_code if patient else None,
        items=[
            InvoiceItemResponse(
                id=it.id,
                item_type=it.item_type,
                item_description=it.item_description,
                quantity=it.quantity,
                unit_price=float(it.unit_price),
                total_price=float(it.total_price),
                reference_id=it.reference_id,
                created_at=it.created_at,
            )
            for it in inv.items
        ],
        payments=[
            PaymentResponse(
                id=p.id,
                invoice_id=p.invoice_id,
                payment_number=p.payment_number,
                amount=float(p.amount),
                payment_method=p.payment_method,
                payment_date=p.payment_date,
                transaction_reference=p.transaction_reference,
                notes=p.notes,
            )
            for p in inv.payments
        ],
        created_at=inv.created_at,
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "ACCOUNTANT", "RECEPTIONIST"])),
):
    patient = await db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    subtotal = sum(item.quantity * item.unit_price for item in payload.items)
    total = subtotal - payload.discount + payload.tax
    if total < 0:
        total = 0.0

    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        patient_id=payload.patient_id,
        appointment_id=payload.appointment_id,
        total_amount=total,
        discount=payload.discount,
        tax=payload.tax,
        paid_amount=0.0,
        balance_amount=total,
        status="PENDING",
        notes=payload.notes,
    )
    db.add(invoice)
    await db.flush()

    for item in payload.items:
        line_total = item.quantity * item.unit_price
        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            item_type=item.item_type.upper(),
            item_description=item.item_description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=line_total,
            reference_id=item.reference_id,
        )
        db.add(inv_item)

    await db.commit()

    stmt = (
        select(Invoice)
        .where(Invoice.id == invoice.id)
        .options(
            selectinload(Invoice.patient),
            selectinload(Invoice.items),
            selectinload(Invoice.payments),
        )
    )
    loaded = (await db.execute(stmt)).scalar_one()
    return format_invoice_response(loaded)


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    patient_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.patient),
            selectinload(Invoice.items),
            selectinload(Invoice.payments),
        )
    )
    if patient_id:
        stmt = stmt.where(Invoice.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter.upper())

    stmt = stmt.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    invoices = result.scalars().all()
    return [format_invoice_response(inv) for inv in invoices]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = (
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.patient),
            selectinload(Invoice.items),
            selectinload(Invoice.payments),
        )
    )
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return format_invoice_response(inv)


@router.post("/invoices/{invoice_id}/payments", response_model=InvoiceResponse)
async def record_payment(
    invoice_id: uuid.UUID,
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "ACCOUNTANT", "RECEPTIONIST"])),
):
    stmt = (
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.patient),
            selectinload(Invoice.items),
            selectinload(Invoice.payments),
        )
    )
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if inv.balance_amount <= 0:
        raise HTTPException(status_code=400, detail="This invoice is already fully paid")

    if payload.amount > float(inv.balance_amount):
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ({payload.amount}) exceeds outstanding balance ({inv.balance_amount})",
        )

    payment = Payment(
        invoice_id=inv.id,
        payment_number=generate_payment_number(),
        amount=payload.amount,
        payment_method=payload.payment_method.upper(),
        payment_date=datetime.now(timezone.utc),
        transaction_reference=payload.transaction_reference,
        notes=payload.notes,
    )
    db.add(payment)

    inv.paid_amount = float(inv.paid_amount) + payload.amount
    inv.balance_amount = float(inv.total_amount) - float(inv.paid_amount)

    if inv.balance_amount <= 0:
        inv.status = "PAID"
    else:
        inv.status = "PARTIAL"

    db.add(inv)
    await db.commit()

    reloaded = (await db.execute(stmt)).scalar_one()
    return format_invoice_response(reloaded)
