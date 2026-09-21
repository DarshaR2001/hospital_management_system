import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.auth import User
from app.models.pharmacy import Medicine, MedicineBatch, PharmacyTransaction
from app.models.emr import Prescription, PrescriptionItem
from app.schemas.pharmacy import (
    MedicineCreate,
    MedicineResponse,
    MedicineBatchCreate,
    MedicineBatchResponse,
    DispensePrescriptionRequest,
)

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])


def format_medicine_response(med: Medicine) -> MedicineResponse:
    batches = [MedicineBatchResponse.model_validate(b) for b in med.batches]
    total_stock = sum(b.quantity for b in med.batches)
    return MedicineResponse(
        id=med.id,
        code=med.code,
        name=med.name,
        generic_name=med.generic_name,
        category=med.category,
        dosage_form=med.dosage_form,
        unit_price=float(med.unit_price),
        reorder_level=med.reorder_level,
        is_active=med.is_active,
        total_stock=total_stock,
        batches=batches,
        created_at=med.created_at,
    )


@router.get("/medicines", response_model=List[MedicineResponse])
async def list_medicines(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Medicine).options(selectinload(Medicine.batches)).where(Medicine.is_active.is_(True))
    if search:
        s = f"%{search}%"
        stmt = stmt.where((Medicine.name.ilike(s)) | (Medicine.code.ilike(s)) | (Medicine.generic_name.ilike(s)))
    if category:
        stmt = stmt.where(Medicine.category.ilike(f"%{category}%"))

    stmt = stmt.order_by(Medicine.name)
    result = await db.execute(stmt)
    medicines = result.scalars().all()
    return [format_medicine_response(m) for m in medicines]


@router.post("/medicines", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(
    payload: MedicineCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "PHARMACIST"])),
):
    existing = (await db.execute(select(Medicine).where(Medicine.code == payload.code))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Medicine with this code already exists")

    med = Medicine(
        code=payload.code,
        name=payload.name,
        generic_name=payload.generic_name,
        category=payload.category,
        dosage_form=payload.dosage_form,
        unit_price=payload.unit_price,
        reorder_level=payload.reorder_level,
        is_active=payload.is_active,
    )
    db.add(med)
    await db.flush()

    if payload.initial_batch_number and payload.initial_quantity and payload.expiry_date:
        batch = MedicineBatch(
            medicine_id=med.id,
            batch_number=payload.initial_batch_number,
            expiry_date=payload.expiry_date,
            quantity=payload.initial_quantity,
            purchase_price=payload.purchase_price or (payload.unit_price * 0.7),
        )
        db.add(batch)
        db.add(PharmacyTransaction(
            medicine_id=med.id,
            batch_id=batch.id,
            transaction_type="PURCHASE",
            quantity=payload.initial_quantity,
            unit_price=payload.unit_price,
            total_amount=payload.unit_price * payload.initial_quantity,
        ))

    await db.commit()
    await db.refresh(med)

    stmt = select(Medicine).where(Medicine.id == med.id).options(selectinload(Medicine.batches))
    loaded = (await db.execute(stmt)).scalar_one()
    return format_medicine_response(loaded)


@router.get("/medicines/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(
    medicine_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Medicine).where(Medicine.id == medicine_id).options(selectinload(Medicine.batches))
    med = (await db.execute(stmt)).scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return format_medicine_response(med)


@router.post("/batches", response_model=MedicineBatchResponse, status_code=status.HTTP_201_CREATED)
async def add_medicine_batch(
    payload: MedicineBatchCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "PHARMACIST"])),
):
    med = await db.get(Medicine, payload.medicine_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    batch = MedicineBatch(**payload.model_dump())
    db.add(batch)
    await db.flush()

    # Log purchase transaction
    db.add(PharmacyTransaction(
        medicine_id=med.id,
        batch_id=batch.id,
        transaction_type="PURCHASE",
        quantity=payload.quantity,
        unit_price=payload.purchase_price,
        total_amount=payload.purchase_price * payload.quantity,
    ))

    await db.commit()
    await db.refresh(batch)
    return batch


@router.get("/low-stock", response_model=List[MedicineResponse])
async def get_low_stock_medicines(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    stmt = select(Medicine).options(selectinload(Medicine.batches)).where(Medicine.is_active.is_(True))
    result = await db.execute(stmt)
    medicines = result.scalars().all()

    low_stock = []
    for m in medicines:
        stock = sum(b.quantity for b in m.batches)
        if stock <= m.reorder_level:
            low_stock.append(format_medicine_response(m))
    return low_stock


@router.post("/dispense")
async def dispense_prescription(
    payload: DispensePrescriptionRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMINISTRATOR", "PHARMACIST"])),
):
    presc = await db.get(Prescription, payload.prescription_id)
    if not presc:
        raise HTTPException(status_code=404, detail="Prescription not found")

    for it in payload.dispense_items:
        batch = await db.get(MedicineBatch, it.batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch {it.batch_id} not found")

        if batch.quantity < it.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock in batch {batch.batch_number}. Available: {batch.quantity}, Requested: {it.quantity}",
            )

        batch.quantity -= it.quantity
        db.add(batch)

        # Mark prescription item as dispensed
        p_item = await db.get(PrescriptionItem, it.prescription_item_id)
        if p_item:
            p_item.is_dispensed = True
            db.add(p_item)

        # Record transaction
        med = await db.get(Medicine, batch.medicine_id)
        unit_price = float(med.unit_price) if med else 0.0
        db.add(PharmacyTransaction(
            medicine_id=batch.medicine_id,
            batch_id=batch.id,
            prescription_id=presc.id,
            transaction_type="DISPENSE",
            quantity=it.quantity,
            unit_price=unit_price,
            total_amount=unit_price * it.quantity,
        ))

    presc.status = "DISPENSED"
    db.add(presc)
    await db.commit()

    return {"message": "Prescription dispensed and inventory updated successfully"}
