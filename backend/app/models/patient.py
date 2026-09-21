import uuid
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.emr import MedicalRecord, Prescription
    from app.models.lab import LabTestRequest
    from app.models.billing import Invoice
    from app.models.inpatient import Admission


class Patient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "patients"

    patient_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # MALE, FEMALE, OTHER
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="patient")
    medical_records: Mapped[List["MedicalRecord"]] = relationship("MedicalRecord", back_populates="patient")
    prescriptions: Mapped[List["Prescription"]] = relationship("Prescription", back_populates="patient")
    lab_requests: Mapped[List["LabTestRequest"]] = relationship("LabTestRequest", back_populates="patient")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="patient")
    admissions: Mapped[List["Admission"]] = relationship("Admission", back_populates="patient")
