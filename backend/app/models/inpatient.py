import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Integer, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.staff import Doctor


class Ward(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wards"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    ward_type: Mapped[str] = mapped_column(String(50), nullable=False)  # General, ICU, CCU, Private, etc.
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    beds: Mapped[List["Bed"]] = relationship("Bed", back_populates="ward", cascade="all, delete-orphan")


class Bed(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "beds"

    ward_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wards.id", ondelete="CASCADE"), index=True, nullable=False)
    bed_number: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="AVAILABLE",
        index=True,
        nullable=False,
    )  # AVAILABLE, OCCUPIED, MAINTENANCE, RESERVED
    daily_rate: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)

    ward: Mapped["Ward"] = relationship("Ward", back_populates="beds")
    admissions: Mapped[List["Admission"]] = relationship("Admission", back_populates="bed")


class Admission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "admissions"

    admission_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True, nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True, nullable=False)
    bed_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("beds.id", ondelete="RESTRICT"), index=True, nullable=False)
    admission_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    discharge_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    admission_reason: Mapped[str] = mapped_column(Text, nullable=False)
    discharge_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="ADMITTED",
        index=True,
        nullable=False,
    )  # ADMITTED, DISCHARGED, TRANSFERRED

    patient: Mapped["Patient"] = relationship("Patient", back_populates="admissions")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="admissions")
    bed: Mapped["Bed"] = relationship("Bed", back_populates="admissions")
