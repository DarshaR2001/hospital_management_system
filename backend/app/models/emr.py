import uuid
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Date, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.staff import Doctor
    from app.models.appointment import Appointment
    from app.models.pharmacy import Medicine, PharmacyTransaction


class MedicalRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "medical_records"

    record_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True, nullable=False)
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"), unique=True, nullable=True)
    record_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    physical_examination: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="medical_records")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="medical_records")
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="medical_record")
    diagnoses: Mapped[List["Diagnosis"]] = relationship("Diagnosis", back_populates="medical_record", cascade="all, delete-orphan")
    treatments: Mapped[List["Treatment"]] = relationship("Treatment", back_populates="medical_record", cascade="all, delete-orphan")
    prescriptions: Mapped[List["Prescription"]] = relationship("Prescription", back_populates="medical_record")


class Diagnosis(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "diagnoses"

    medical_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medical_records.id", ondelete="CASCADE"), index=True, nullable=False)
    icd_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    diagnosis_name: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis_type: Mapped[str] = mapped_column(String(20), default="PRIMARY", nullable=False)  # PRIMARY, SECONDARY, PROVISIONAL
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    medical_record: Mapped["MedicalRecord"] = relationship("MedicalRecord", back_populates="diagnoses")


class Treatment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "treatments"

    medical_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medical_records.id", ondelete="CASCADE"), index=True, nullable=False)
    treatment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, COMPLETED

    medical_record: Mapped["MedicalRecord"] = relationship("MedicalRecord", back_populates="treatments")


class Prescription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prescriptions"

    prescription_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    medical_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medical_records.id", ondelete="CASCADE"), index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, DISPENSED, CANCELLED
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    medical_record: Mapped["MedicalRecord"] = relationship("MedicalRecord", back_populates="prescriptions")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="prescriptions")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="prescriptions")
    items: Mapped[List["PrescriptionItem"]] = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    pharmacy_transactions: Mapped[List["PharmacyTransaction"]] = relationship("PharmacyTransaction", back_populates="prescription")


class PrescriptionItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prescription_items"

    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True, nullable=False)
    medicine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medicines.id", ondelete="RESTRICT"), index=True, nullable=False)
    dosage: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "500mg"
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "1-0-1", "Twice daily"
    duration: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "5 days"
    instructions: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_dispensed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="items")
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="prescription_items")
