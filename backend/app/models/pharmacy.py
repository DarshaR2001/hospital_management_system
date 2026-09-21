import uuid
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Integer, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.emr import Prescription, PrescriptionItem


class Medicine(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "medicines"

    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    generic_name: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Antibiotic, Analgesic, etc.
    dosage_form: Mapped[str] = mapped_column(String(30), nullable=False)  # Tablet, Syrup, Injection, etc.
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    batches: Mapped[List["MedicineBatch"]] = relationship("MedicineBatch", back_populates="medicine", cascade="all, delete-orphan")
    prescription_items: Mapped[List["PrescriptionItem"]] = relationship("PrescriptionItem", back_populates="medicine")
    transactions: Mapped[List["PharmacyTransaction"]] = relationship("PharmacyTransaction", back_populates="medicine")


class MedicineBatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "medicine_batches"

    medicine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"), index=True, nullable=False)
    batch_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)

    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="batches")
    transactions: Mapped[List["PharmacyTransaction"]] = relationship("PharmacyTransaction", back_populates="batch")


class PharmacyTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pharmacy_transactions"

    medicine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medicines.id", ondelete="RESTRICT"), index=True, nullable=False)
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("medicine_batches.id", ondelete="SET NULL"), nullable=True)
    prescription_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PURCHASE, DISPENSE, ADJUSTMENT, RETURN
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="transactions")
    batch: Mapped[Optional["MedicineBatch"]] = relationship("MedicineBatch", back_populates="transactions")
    prescription: Mapped[Optional["Prescription"]] = relationship("Prescription", back_populates="pharmacy_transactions")
