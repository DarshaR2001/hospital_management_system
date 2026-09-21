import uuid
from datetime import date, time
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Date, Time, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.staff import Doctor
    from app.models.emr import MedicalRecord
    from app.models.lab import LabTestRequest
    from app.models.billing import Invoice


class Appointment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "appointments"

    appointment_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True, nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="SCHEDULED",
        index=True,
        nullable=False,
    )  # SCHEDULED, CONFIRMED, CHECKED_IN, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")
    medical_record: Mapped[Optional["MedicalRecord"]] = relationship("MedicalRecord", back_populates="appointment", uselist=False)
    lab_requests: Mapped[List["LabTestRequest"]] = relationship("LabTestRequest", back_populates="appointment")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="appointment")

    __table_args__ = (
        Index("ix_doctor_date_time", "doctor_id", "appointment_date", "appointment_time"),
    )
