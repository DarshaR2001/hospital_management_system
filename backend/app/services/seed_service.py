from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.auth import Role, User
from app.models.staff import Department
from app.models.lab import LaboratoryTest
from app.models.pharmacy import Medicine, MedicineBatch
from app.models.inpatient import Ward, Bed


DEFAULT_ROLES = [
    ("ADMINISTRATOR", "System Administrator with full access"),
    ("DOCTOR", "Medical Doctor with access to EMR, prescriptions, lab requests"),
    ("NURSE", "Nurse with access to admissions, vitals, patient monitoring"),
    ("RECEPTIONIST", "Receptionist with access to patient registration and appointment booking"),
    ("LAB_STAFF", "Laboratory technician with access to lab tests and results"),
    ("PHARMACIST", "Pharmacist with access to inventory, dispensing, and prescriptions"),
    ("ACCOUNTANT", "Accountant with access to billing, invoices, and payments"),
]

DEFAULT_DEPARTMENTS = [
    ("General Medicine", "GENMED", "General adult health conditions and primary care"),
    ("Cardiology", "CARDIO", "Heart and cardiovascular system care"),
    ("Pediatrics", "PEDIAT", "Infant, child, and adolescent medical care"),
    ("Orthopedics", "ORTHO", "Musculoskeletal system and bone health"),
    ("Emergency", "EMERG", "24/7 acute trauma and emergency care"),
    ("Laboratory & Pathology", "LABPATH", "Diagnostic testing and sample analysis"),
    ("Pharmacy Services", "PHARM", "Medication distribution and pharmaceutical care"),
]

DEFAULT_LAB_TESTS = [
    ("CBC001", "Complete Blood Count (CBC)", "Hematology", 450.00, "Normal: 4.5-11.0 x10^3/uL", "/uL"),
    ("LIP001", "Lipid Profile", "Biochemistry", 850.00, "Cholesterol < 200 mg/dL", "mg/dL"),
    ("FBS001", "Fasting Blood Sugar (FBS)", "Biochemistry", 200.00, "70 - 99 mg/dL", "mg/dL"),
    ("LFT001", "Liver Function Test (LFT)", "Biochemistry", 1100.00, "ALT 7-56 U/L, AST 10-40 U/L", "U/L"),
    ("KFT001", "Kidney Function Test (KFT)", "Biochemistry", 950.00, "Creatinine 0.7-1.3 mg/dL", "mg/dL"),
    ("UR001", "Urine Routine Examination", "Pathology", 250.00, "Clear, Straw colored", "N/A"),
    ("CXR001", "Chest X-Ray PA View", "Radiology", 600.00, "Normal lung fields and cardiac shadow", "N/A"),
]

DEFAULT_MEDICINES = [
    ("MED001", "Paracetamol", "Acetaminophen", "Analgesic / Antipyretic", "Tablet", 5.00, 100),
    ("MED002", "Amoxicillin", "Amoxicillin Trihydrate", "Antibiotic", "Capsule", 12.00, 50),
    ("MED003", "Metformin", "Metformin HCl", "Antidiabetic", "Tablet", 8.00, 80),
    ("MED004", "Ibuprofen", "Ibuprofen", "NSAID", "Tablet", 6.50, 60),
    ("MED005", "Omeprazole", "Omeprazole", "Antacid / PPI", "Capsule", 15.00, 50),
    ("MED006", "Cetirizine", "Cetirizine Dihydrochloride", "Antihistamine", "Tablet", 4.00, 100),
    ("MED007", "Azithromycin", "Azithromycin Dihydrate", "Antibiotic", "Tablet", 25.00, 40),
]

DEFAULT_WARDS = [
    ("General Ward Male", "General", "1st Floor", 10),
    ("General Ward Female", "General", "1st Floor", 10),
    ("Intensive Care Unit (ICU)", "ICU", "2nd Floor", 4),
    ("Emergency Ward", "Emergency", "Ground Floor", 6),
]


async def seed_database(db: AsyncSession) -> dict:
    summary = {}

    # 1. Seed Roles
    roles_created = 0
    role_map = {}
    for name, desc in DEFAULT_ROLES:
        stmt = select(Role).where(Role.name == name)
        res = await db.execute(stmt)
        role = res.scalar_one_or_none()
        if not role:
            role = Role(name=name, description=desc, is_active=True)
            db.add(role)
            await db.flush()
            roles_created += 1
        role_map[name] = role
    summary["roles_seeded"] = roles_created

    # 2. Seed Default Administrator
    admin_stmt = select(User).where(User.email == "admin@hospital.com")
    admin_res = await db.execute(admin_stmt)
    admin_user = admin_res.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            email="admin@hospital.com",
            hashed_password=get_password_hash("Admin@123456"),
            full_name="System Administrator",
            phone="+91 9876543210",
            role_id=role_map["ADMINISTRATOR"].id,
            is_active=True,
        )
        db.add(admin_user)
        summary["admin_user"] = "Created admin@hospital.com / Admin@123456"
    else:
        summary["admin_user"] = "Already exists"

    # 3. Seed Departments
    dept_created = 0
    for name, code, desc in DEFAULT_DEPARTMENTS:
        stmt = select(Department).where(Department.code == code)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            db.add(Department(name=name, code=code, description=desc, is_active=True))
            dept_created += 1
    summary["departments_seeded"] = dept_created

    # 4. Seed Lab Tests
    tests_created = 0
    for code, name, cat, price, normal, units in DEFAULT_LAB_TESTS:
        stmt = select(LaboratoryTest).where(LaboratoryTest.test_code == code)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            db.add(LaboratoryTest(
                test_code=code,
                test_name=name,
                category=cat,
                price=price,
                normal_range=normal,
                units=units,
                is_active=True,
            ))
            tests_created += 1
    summary["lab_tests_seeded"] = tests_created

    # 5. Seed Medicines & Batches
    meds_created = 0
    for code, name, gen, cat, dosage, price, reorder in DEFAULT_MEDICINES:
        stmt = select(Medicine).where(Medicine.code == code)
        res = await db.execute(stmt)
        med = res.scalar_one_or_none()
        if not med:
            med = Medicine(
                code=code,
                name=name,
                generic_name=gen,
                category=cat,
                dosage_form=dosage,
                unit_price=price,
                reorder_level=reorder,
                is_active=True,
            )
            db.add(med)
            await db.flush()
            # Add initial batch
            db.add(MedicineBatch(
                medicine_id=med.id,
                batch_number=f"BATCH-{code}-2026",
                expiry_date=date.today() + timedelta(days=365),
                quantity=200,
                purchase_price=price * 0.7,
            ))
            meds_created += 1
    summary["medicines_seeded"] = meds_created

    # 6. Seed Wards & Beds
    wards_created = 0
    for name, w_type, floor, cap in DEFAULT_WARDS:
        stmt = select(Ward).where(Ward.name == name)
        res = await db.execute(stmt)
        ward = res.scalar_one_or_none()
        if not ward:
            ward = Ward(name=name, ward_type=w_type, floor=floor, capacity=cap, is_active=True)
            db.add(ward)
            await db.flush()
            # Add beds
            for i in range(1, 5):
                prefix = name[:3].upper()
                db.add(Bed(
                    ward_id=ward.id,
                    bed_number=f"{prefix}-{i:02d}",
                    status="AVAILABLE",
                    daily_rate=1500.00 if w_type == "General" else 4500.00,
                ))
            wards_created += 1
    summary["wards_seeded"] = wards_created

    await db.commit()
    return summary
