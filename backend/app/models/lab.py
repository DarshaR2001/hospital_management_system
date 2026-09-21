import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.staff import Doctor
    from app.models.appointment import Appointment
    from app.models.auth import User


class LaboratoryTest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "laboratory_tests"

    test_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    test_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Hematology, Biochemistry, etc.
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    normal_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    units: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    results: Mapped[List["LabResult"]] = relationship("LabResult", back_populates="test")


class LabTestRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lab_test_requests"

    request_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True, nullable=False)
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default="REQUESTED",
        index=True,
        nullable=False,
    )  # REQUESTED, SAMPLE_COLLECTED, IN_PROGRESS, COMPLETED, CANCELLED
    clinical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sample_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="lab_requests")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="lab_requests")
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="lab_requests")
    results: Mapped[List["LabResult"]] = relationship("LabResult", back_populates="request", cascade="all, delete-orphan")


class LabResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lab_results"

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lab_test_requests.id", ondelete="CASCADE"), index=True, nullable=False)
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("laboratory_tests.id", ondelete="RESTRICT"), index=True, nullable=False)
    result_value: Mapped[str] = mapped_column(String(100), nullable=False)
    normal_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)  # NORMAL, ABNORMAL, CRITICAL, PENDING
    performed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    request: Mapped["LabTestRequest"] = relationship("LabTestRequest", back_populates="results")
    test: Mapped["LaboratoryTest"] = relationship("LaboratoryTest", back_populates="results")
    performed_by: Mapped[Optional["User"]] = relationship("User")
