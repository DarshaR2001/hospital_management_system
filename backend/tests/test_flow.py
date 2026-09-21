import pytest
import uuid
from datetime import date

@pytest.mark.asyncio
async def test_full_hospital_workflow(client):
    print("\n[STEP 1] Logging in as Admin...")
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hospital.com", "password": "Admin@123456"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(" -> Admin logged in successfully.")

    print("[STEP 2] Fetching Departments...")
    dept_res = await client.get("/api/v1/departments", headers=auth_headers)
    assert dept_res.status_code == 200
    departments = dept_res.json()
    assert len(departments) > 0
    dept_id = departments[0]["id"]
    print(f" -> Found {len(departments)} departments.")

    print("[STEP 3] Registering Doctor...")
    doc_suffix = uuid.uuid4().hex[:6]
    doc_res = await client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "email": f"dr.{doc_suffix}@hospital.com",
            "password": "Doctor@123456",
            "full_name": f"Gregory House {doc_suffix}",
            "specialization": "Internal Medicine",
            "license_number": f"LIC-{doc_suffix.upper()}",
            "consultation_fee": 500.00,
            "room_number": "Room 101",
            "department_id": dept_id,
        },
    )
    assert doc_res.status_code == 201
    doctor = doc_res.json()
    doctor_id = doctor["id"]
    print(f" -> Created doctor: {doctor['doctor_name']}")

    print("[STEP 4] Registering Patient...")
    pat_res = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "first_name": "John",
            "last_name": "Doe",
            "gender": "MALE",
            "dob": "1990-05-15",
            "blood_group": "O+",
            "phone": "+91 9988776655",
            "email": f"john.{doc_suffix}@example.com",
            "address": "123 Main St, Springfield",
            "emergency_contact": "Jane Doe",
            "emergency_phone": "+91 9988776654",
        },
    )
    assert pat_res.status_code == 201
    patient = pat_res.json()
    patient_id = patient["id"]
    print(f" -> Created patient: {patient['patient_code']}")

    print("[STEP 5] Booking Appointment...")
    today_str = date.today().isoformat()
    appt_res = await client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": today_str,
            "appointment_time": "10:00:00",
            "reason": "Persistent fever and headache",
        },
    )
    assert appt_res.status_code == 201
    appointment = appt_res.json()
    appt_id = appointment["id"]
    print(f" -> Booked appointment: {appointment['appointment_number']}")

    print("[STEP 6] Testing Double Booking Prevention...")
    duplicate_res = await client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": today_str,
            "appointment_time": "10:00:00",
            "reason": "Another checkup",
        },
    )
    assert duplicate_res.status_code == 409
    print(" -> Double booking prevented (409 Conflict).")

    print("[STEP 7] Checking in Appointment...")
    status_res = await client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        headers=auth_headers,
        json={"status": "CHECKED_IN", "notes": "Patient arrived on time"},
    )
    assert status_res.status_code == 200
    print(" -> Appointment checked in.")

    print("[STEP 8] Querying Medicines...")
    med_res = await client.get("/api/v1/pharmacy/medicines", headers=auth_headers)
    assert med_res.status_code == 200
    medicines = med_res.json()
    assert len(medicines) > 0
    paracetamol = next((m for m in medicines if "Paracetamol" in m["name"]), medicines[0])
    print(f" -> Found medicine: {paracetamol['name']}")

    print("[STEP 9] Conducting EMR Consultation...")
    consult_res = await client.post(
        "/api/v1/emr/consultation",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_id": appt_id,
            "chief_complaint": "Acute onset high fever with body aches for 3 days",
            "physical_examination": "Temperature 102F, BP 120/80, Chest clear",
            "notes": "Suspected viral infection",
            "diagnoses": [
                {
                    "diagnosis_name": "Viral Fever",
                    "icd_code": "A99",
                    "diagnosis_type": "PRIMARY",
                }
            ],
            "treatments": [
                {
                    "treatment_name": "Symptomatic relief and adequate hydration",
                    "instructions": "Drink 3 liters of fluids daily",
                    "status": "IN_PROGRESS",
                }
            ],
            "prescription_items": [
                {
                    "medicine_id": paracetamol["id"],
                    "dosage": "500mg",
                    "frequency": "1-0-1",
                    "duration": "3 days",
                    "instructions": "Take after meals",
                    "quantity": 6,
                }
            ],
        },
    )
    assert consult_res.status_code == 201
    consultation = consult_res.json()
    presc_id = consultation["prescriptions"][0]["id"]
    presc_item_id = consultation["prescriptions"][0]["items"][0]["id"]
    print(" -> EMR Consultation complete.")

    print("[STEP 10] Requesting Lab Test...")
    lab_tests_res = await client.get("/api/v1/lab/tests", headers=auth_headers)
    assert lab_tests_res.status_code == 200
    cbc_test = lab_tests_res.json()[0]

    lab_req_res = await client.post(
        "/api/v1/lab/requests",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_id": appt_id,
            "test_ids": [cbc_test["id"]],
            "clinical_notes": "Rule out dengue / platelet drop",
            "sample_type": "Blood",
        },
    )
    assert lab_req_res.status_code == 201
    lab_req = lab_req_res.json()
    lab_req_id = lab_req["id"]

    sample_res = await client.patch(
        f"/api/v1/lab/requests/{lab_req_id}/sample",
        headers=auth_headers,
        json={"sample_type": "Whole Blood (EDTA)"},
    )
    assert sample_res.status_code == 200

    results_res = await client.post(
        f"/api/v1/lab/requests/{lab_req_id}/results",
        headers=auth_headers,
        json=[
            {
                "test_id": cbc_test["id"],
                "result_value": "Platelet 210,000 /uL, WBC 6,200 /uL",
                "status": "NORMAL",
                "remarks": "Normal counts",
            }
        ],
    )
    assert results_res.status_code == 200
    print(" -> Lab test flow complete.")

    print("[STEP 11] Dispensing Pharmacy Prescription...")
    batch_id = paracetamol["batches"][0]["id"]
    dispense_res = await client.post(
        "/api/v1/pharmacy/dispense",
        headers=auth_headers,
        json={
            "prescription_id": presc_id,
            "dispense_items": [
                {
                    "prescription_item_id": presc_item_id,
                    "batch_id": batch_id,
                    "quantity": 6,
                }
            ],
        },
    )
    assert dispense_res.status_code == 200
    print(" -> Prescription dispensed.")

    print("[STEP 12] Creating Invoice & Payment...")
    inv_res = await client.post(
        "/api/v1/billing/invoices",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "appointment_id": appt_id,
            "discount": 50.00,
            "tax": 25.00,
            "notes": "Consultation + CBC + Pharmacy",
            "items": [
                {
                    "item_type": "CONSULTATION",
                    "item_description": "Dr. House Consultation Fee",
                    "quantity": 1,
                    "unit_price": 500.00,
                },
                {
                    "item_type": "LAB_TEST",
                    "item_description": f"Lab: {cbc_test['test_name']}",
                    "quantity": 1,
                    "unit_price": float(cbc_test["price"]),
                },
                {
                    "item_type": "PHARMACY",
                    "item_description": f"{paracetamol['name']} (Qty 6)",
                    "quantity": 6,
                    "unit_price": float(paracetamol["unit_price"]),
                },
            ],
        },
    )
    assert inv_res.status_code == 201
    invoice = inv_res.json()
    invoice_id = invoice["id"]

    pay_res = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/payments",
        headers=auth_headers,
        json={
            "amount": invoice["balance_amount"],
            "payment_method": "UPI",
            "transaction_reference": "UPI-REF-998822",
            "notes": "Paid in full via GPay",
        },
    )
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "PAID"
    print(" -> Invoice created and paid.")

    print("[STEP 13] Checking Dashboard & Patient History...")
    dash_res = await client.get("/api/v1/reports/dashboard-stats", headers=auth_headers)
    assert dash_res.status_code == 200

    history_res = await client.get(f"/api/v1/patients/{patient_id}/history", headers=auth_headers)
    assert history_res.status_code == 200
    print(" -> ALL 13 STEPS SUCCEEDED PERFECTLY!\n")
