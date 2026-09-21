import uuid
from datetime import date, time
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Numeric, Date, Time, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.appointment import Appointment
    from app.models.emr import MedicalRecord, Prescription
    from app.models.lab import LabTestRequest
    from app.models.inpatient import Admission


class Department(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="department")


class Employee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employees"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    qualification: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="employee")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="employees")
    doctor: Mapped[Optional["Doctor"]] = relationship("Doctor", back_populates="employee", uselist=False)


class Doctor(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "doctors"

    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    consultation_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    room_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="doctor")
    schedules: Mapped[List["DoctorSchedule"]] = relationship("DoctorSchedule", back_populates="doctor", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="doctor")
    medical_records: Mapped[List["MedicalRecord"]] = relationship("MedicalRecord", back_populates="doctor")
    prescriptions: Mapped[List["Prescription"]] = relationship("Prescription", back_populates="doctor")
    lab_requests: Mapped[List["LabTestRequest"]] = relationship("LabTestRequest", back_populates="doctor")
    admissions: Mapped[List["Admission"]] = relationship("Admission", back_populates="doctor")


class DoctorSchedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "doctor_schedules"

    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="schedules")
