import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.appointment import Appointment


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True, nullable=False)
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    balance_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        index=True,
        nullable=False,
    )  # PENDING, PARTIAL, PAID, CANCELLED
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="invoices")
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="invoices")
    items: Mapped[List["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)  # CONSULTATION, LAB_TEST, PHARMACY, ADMISSION, OTHER
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="RESTRICT"), index=True, nullable=False)
    payment_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)  # CASH, CARD, UPI, BANK_TRANSFER, INSURANCE
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
