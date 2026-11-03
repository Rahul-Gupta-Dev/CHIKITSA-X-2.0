import urllib.request
import urllib.error
import json
import time
import sqlite3
import os

BASE_URL = "http://127.0.0.1:8000/api"
DB_PATH = os.path.join(os.path.dirname(__file__), "chikitsax.db")

def api_call(method: str, endpoint: str, data=None, token: str = None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            try:
                parsed = json.loads(content.decode("utf-8"))
            except Exception:
                parsed = content
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            parsed = json.loads(content.decode("utf-8"))
        except Exception:
            parsed = {"detail": content.decode("utf-8", errors="ignore")}
        return e.code, parsed

def query_db(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

def main():
    print("=========================================================================")
    print("CHIKITSA-X Phase 4.1: Doctor Consultation Backend Integration Test Suite")
    print("=========================================================================")

    ts = int(time.time())
    passed_tests = 0
    total_tests = 11

    # --- Setup Actors ---
    # 1. Register Patient A
    pA_email = f"patientA_{ts}@chikitsax.test"
    st, reg_res = api_call("POST", "/auth/register", {
        "name": f"Anjali Deshmukh {ts}",
        "fullName": f"Anjali Deshmukh {ts}",
        "email": pA_email,
        "phone": "+91 98222 11111",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200, f"Registration of Patient A failed: {reg_res}"
    pA_token = reg_res["accessToken"]
    pA_id = reg_res["user"]["id"]

    # 2. Register Patient B (for unauthorized access tests)
    pB_email = f"patientB_{ts}@chikitsax.test"
    st, reg_res_b = api_call("POST", "/auth/register", {
        "name": f"Vikram Deshmukh {ts}",
        "fullName": f"Vikram Deshmukh {ts}",
        "email": pB_email,
        "phone": "+91 98333 22222",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200, f"Registration of Patient B failed: {reg_res_b}"
    pB_token = reg_res_b["accessToken"]
    pB_id = reg_res_b["user"]["id"]

    # 3. Authenticate Doctor 1 (Dr. Rajesh Kulkarni - doc-1)
    st, d1_res = api_call("POST", "/auth/login", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    assert st == 200, f"Doctor 1 login failed: {d1_res}"
    d1_token = d1_res["accessToken"]
    d1_id = d1_res["user"]["id"]

    # 3.5 Authenticate Hospital Admin (CarePlus - hosp-1)
    st, h_res = api_call("POST", "/auth/login", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_ADMIN"
    })
    assert st == 200, f"Hospital admin login failed: {h_res}"
    h_token = h_res["accessToken"]

    # 4. Register Doctor 2 (Dr. Ananya Roy - doc-2 / other doctor) via authorized Hospital Admin
    d2_email = f"doctor2_{ts}@chikitsax.test"
    st, reg_res_d2 = api_call("POST", "/auth/register", {
        "name": "Dr. Ananya Roy",
        "fullName": "Dr. Ananya Roy",
        "email": d2_email,
        "phone": "+91 98444 33333",
        "password": "Password123!",
        "role": "DOCTOR",
        "hospitalId": "hosp-1"
    }, token=h_token)
    assert st == 200, f"Registration of Doctor 2 failed: {reg_res_d2}"
    d2_token = reg_res_d2["accessToken"]
    d2_id = reg_res_d2["user"]["id"]

    print(" Actors authenticated:")
    print(f"  - Patient A: {pA_id}")
    print(f"  - Patient B: {pB_id}")
    print(f"  - Doctor 1 (Assigned): {d1_id} (Dr. Rajesh Kulkarni)")
    print(f"  - Doctor 2 (Unassigned): {d2_id} (Dr. Ananya Roy)")

    # -------------------------------------------------------------------------
    # TEST 1: Unauthenticated consultation creation rejected with HTTP 401
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Unauthenticated Consultation Creation ---")
    st, res = api_call("POST", "/consultations", {
        "appointment_id": "opd-dummy-1",
        "clinical_notes": "Attempting unauthenticated access",
        "diagnosis": "None",
        "treatment_plan": "None"
    })
    print(f"HTTP Status: {st}, Detail: {res.get('detail')}")
    assert st == 401, f"Expected 401 for unauthenticated request, got {st}"
    assert "Authentication required" in res.get("detail", ""), f"Unexpected error detail: {res}"
    print("PASS: Unauthenticated consultation creation rejected with HTTP 401")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 2: Patient cannot finalize consultation (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Patient Role Cannot Finalize Consultation ---")
    st, res = api_call("POST", "/consultations", {
        "appointment_id": "opd-dummy-1",
        "clinical_notes": "Patient attempting to finalize own consultation",
        "diagnosis": "None",
        "treatment_plan": "None"
    }, token=pA_token)
    print(f"HTTP Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 for patient role, got {st}"
    assert "Only doctors can finalize" in res.get("detail", ""), f"Unexpected error detail: {res}"
    print("PASS: Patient forbidden from finalizing consultation (HTTP 403)")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 3: Doctor cannot finalize another doctor's appointment (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Doctor Assignment Validation ---")
    # Book an appointment for Patient A assigned to doc-2 (Dr. Ananya Roy)
    app_date_doc2 = f"2027-06-{(ts % 20) + 1:02d}"
    slot_time_doc2 = f"{(ts % 10) + 1:02d}:{(ts % 50) + 10:02d} AM"
    st, app_doc2 = api_call("POST", "/opd", {
        "patient_id": pA_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-2",
        "department": "Neurology",
        "appointment_date": app_date_doc2,
        "appointment_time": slot_time_doc2
    }, token=pA_token)
    assert st == 200, f"Booking appointment for doc-2 failed: {app_doc2}"
    app_doc2_id = app_doc2["id"]

    # Dr. Rajesh (d1_token) attempts to finalize Dr. Ananya's appointment
    st, res = api_call("POST", "/consultations", {
        "appointment_id": app_doc2_id,
        "clinical_notes": "Dr. Rajesh trying to finalize Dr. Ananya's patient",
        "diagnosis": "Headache",
        "treatment_plan": "Rest"
    }, token=d1_token)
    print(f"HTTP Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 for unassigned doctor, got {st}"
    assert "not the assigned doctor" in res.get("detail", ""), f"Unexpected error detail: {res}"
    print("PASS: Unassigned doctor cannot finalize appointment (HTTP 403)")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 4: Invalid appointment ID returns HTTP 404
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Non-existent Appointment ID ---")
    st, res = api_call("POST", "/consultations", {
        "appointment_id": "opd-nonexistent-99999",
        "clinical_notes": "Checking non-existent appointment",
        "diagnosis": "Test",
        "treatment_plan": "Test"
    }, token=d1_token)
    print(f"HTTP Status: {st}, Detail: {res.get('detail')}")
    assert st == 404, f"Expected 404 for missing appointment, got {st}"
    assert "Appointment not found" in res.get("detail", ""), f"Unexpected error detail: {res}"
    print("PASS: Non-existent appointment ID returns HTTP 404")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 5: Conflicting patient ID returns HTTP 400
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Conflicting Patient ID Validation ---")
    # Book appointment for Patient A with Dr. Rajesh (doc-1)
    slot_time_doc1 = f"{(ts % 11) + 1:02d}:{(ts % 40) + 15:02d} PM"
    st, app_doc1 = api_call("POST", "/opd", {
        "patient_id": pA_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": f"2027-07-{(ts % 20) + 1:02d}",
        "appointment_time": slot_time_doc1
    }, token=pA_token)
    assert st == 200, f"Booking appointment for doc-1 failed: {app_doc1}"
    app_doc1_id = app_doc1["id"]

    # Dr. Rajesh submits consultation with mismatched patient ID (Patient B's ID)
    st, res = api_call("POST", "/consultations", {
        "appointment_id": app_doc1_id,
        "patient_id": pB_id, # Conflicting!
        "clinical_notes": "Mismatched patient id test",
        "diagnosis": "Hypertension",
        "treatment_plan": "Monitor BP"
    }, token=d1_token)
    print(f"HTTP Status: {st}, Detail: {res.get('detail')}")
    assert st == 400, f"Expected 400 for conflicting patient ID, got {st}"
    assert "Conflicting patient ID" in res.get("detail", ""), f"Unexpected error detail: {res}"
    print("PASS: Conflicting patient ID rejected with HTTP 400")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 6: Assigned doctor finalizes valid appointment (HTTP 200)
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Assigned Doctor Finalizes Valid Consultation ---")
    st, cons_res = api_call("POST", "/consultations", {
        "appointment_id": app_doc1_id,
        "patient_id": pA_id,
        "clinical_notes": "Patient presented with mild effort-induced chest tightness. Normal sinus rhythm.",
        "diagnosis": "Suspected Angina Pectoris / Ischemic Heart Disease",
        "treatment_plan": "Advised 2D Echocardiogram, Trop-I, and Coronary Angiography evaluation.",
        "prescription_medicines": [
            {"name": "Sorbitrate 5mg", "dosage": "Sublingual PRN", "duration": "5 days"},
            {"name": "Aspirin 75mg", "dosage": "1-0-0 (Post Meal)", "duration": "30 days"}
        ],
        "investigations_ordered": ["2D Echocardiogram", "Troponin-I Level"]
    }, token=d1_token)
    print(f"HTTP Status: {st}, Response: {cons_res}")
    assert st == 200, f"Consultation finalization failed: {cons_res}"
    assert cons_res["appointmentId"] == app_doc1_id, f"Mismatched appointmentId: {cons_res}"
    assert cons_res["status"] == "COMPLETED", f"Expected COMPLETED status: {cons_res}"
    assert cons_res["diagnosis"] == "Suspected Angina Pectoris / Ischemic Heart Disease"
    assert len(cons_res["prescriptionMedicines"]) == 2
    assert len(cons_res["investigationsOrdered"]) == 2
    cons_id = cons_res["id"]
    print(f"PASS: Consultation {cons_id} finalized successfully with HTTP 200")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 7: Persistence and State Transition in SQLite Database
    # -------------------------------------------------------------------------
    print("\n--- TEST 7: SQLite DB State Verification & Consultation Read ---")
    # Verify consultations table row
    cons_rows = query_db("SELECT id, appointment_id, patient_id, doctor_id, status, diagnosis FROM consultations WHERE appointment_id = ?", (app_doc1_id,))
    assert len(cons_rows) == 1, f"Expected 1 consultation row in DB, found {len(cons_rows)}"
    db_c_id, db_c_appid, db_c_pid, db_c_docid, db_c_status, db_c_diag = cons_rows[0]
    assert db_c_appid == app_doc1_id
    assert db_c_status == "COMPLETED"
    print(f"  ✓ Consultations table row persisted: ID={db_c_id}, status={db_c_status}, diagnosis={db_c_diag}")

    # Verify opd_appointments table status is COMPLETED
    opd_rows = query_db("SELECT id, status FROM opd_appointments WHERE id = ?", (app_doc1_id,))
    assert len(opd_rows) == 1
    assert opd_rows[0][1] == "COMPLETED", f"Expected OPD status COMPLETED, got {opd_rows[0][1]}"
    print(f"  ✓ OPD Appointment status updated to: {opd_rows[0][1]}")

    # Verify patients table care_stage is advanced to 8
    pat_rows = query_db("SELECT id, user_id, care_stage FROM patients WHERE user_id = ? OR id = ?", (pA_id, pA_id))
    assert len(pat_rows) >= 1
    assert pat_rows[0][2] == 8, f"Expected patient care_stage == 8, got {pat_rows[0][2]}"
    print(f"  ✓ Patient care_stage advanced to: {pat_rows[0][2]}")

    # Verify GET /api/consultations/{appointment_id} for Patient A
    st, read_pA = api_call("GET", f"/consultations/{app_doc1_id}", token=pA_token)
    assert st == 200, f"Patient A read consultation failed: {read_pA}"
    assert read_pA["id"] == cons_id
    print("  ✓ Patient A retrieved their consultation successfully via GET /api/consultations/{appointment_id}")

    # Verify GET /api/consultations/{appointment_id} for Assigned Doctor
    st, read_doc = api_call("GET", f"/consultations/{app_doc1_id}", token=d1_token)
    assert st == 200, f"Doctor read consultation failed: {read_doc}"
    assert read_doc["id"] == cons_id
    print("  ✓ Assigned Doctor retrieved consultation successfully")
    print("PASS: SQLite persistence and read authorization verified")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 8: Duplicate finalization rejected with HTTP 409 Conflict
    # -------------------------------------------------------------------------
    print("\n--- TEST 8: Duplicate Finalization Prevention ---")
    st, dup_res = api_call("POST", "/consultations", {
        "appointment_id": app_doc1_id,
        "patient_id": pA_id,
        "clinical_notes": "Attempting second finalization for the same appointment",
        "diagnosis": "Already Finalized",
        "treatment_plan": "None"
    }, token=d1_token)
    print(f"HTTP Status: {st}, Detail: {dup_res.get('detail')}")
    assert st == 409, f"Expected 409 Conflict on duplicate finalization, got {st}"
    assert "already been finalized" in dup_res.get("detail", ""), f"Unexpected detail: {dup_res}"
    print("PASS: Duplicate finalization prevented with HTTP 409 Conflict")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 9: Unauthorized Read Access Rejected (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- TEST 9: Unauthorized Read Access Control ---")
    # Patient B attempts to read Patient A's consultation
    st, res_b = api_call("GET", f"/consultations/{app_doc1_id}", token=pB_token)
    print(f"Patient B Read -> HTTP Status: {st}, Detail: {res_b.get('detail')}")
    assert st == 403, f"Expected 403 for unauthorized patient, got {st}"
    assert "another patient" in res_b.get("detail", ""), f"Unexpected detail: {res_b}"

    # Doctor 2 (unassigned and without active consent) attempts to read Patient A's consultation
    st, res_d2 = api_call("GET", f"/consultations/{app_doc1_id}", token=d2_token)
    print(f"Doctor 2 Read -> HTTP Status: {st}, Detail: {res_d2.get('detail')}")
    assert st == 403, f"Expected 403 for unassigned doctor without consent, got {st}"
    assert "lacks active patient consent" in res_d2.get("detail", ""), f"Unexpected detail: {res_d2}"
    print("PASS: Unauthorized patient and doctor reads rejected with HTTP 403")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 10: Failed consultation attempt does not advance care stage or change appointment status
    # -------------------------------------------------------------------------
    print("\n--- TEST 10: Validation Failure Guarantees No State Mutation ---")
    # Register Patient C
    pC_email = f"patientC_{ts}@chikitsax.test"
    st, reg_res_c = api_call("POST", "/auth/register", {
        "name": f"Kavita Verma {ts}",
        "fullName": f"Kavita Verma {ts}",
        "email": pC_email,
        "phone": "+91 98555 44444",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200
    pC_token = reg_res_c["accessToken"]
    pC_id = reg_res_c["user"]["id"]

    # Check Patient C initial care stage
    c_pat_initial = query_db("SELECT care_stage FROM patients WHERE user_id = ?", (pC_id,))
    assert c_pat_initial[0][0] == 1, f"Expected initial care_stage 1, got {c_pat_initial[0][0]}"

    # Book appointment with Dr. Rajesh (which advances care stage to 6)
    slot_time_doc1_c = f"{(ts % 10) + 1:02d}:{(ts % 30) + 20:02d} PM"
    st, app_doc1_c = api_call("POST", "/opd", {
        "patient_id": pC_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": f"2027-08-{(ts % 20) + 1:02d}",
        "appointment_time": slot_time_doc1_c
    }, token=pC_token)
    assert st == 200
    app_c_id = app_doc1_c["id"]

    c_pat_booked = query_db("SELECT care_stage FROM patients WHERE user_id = ?", (pC_id,))
    assert c_pat_booked[0][0] == 6, f"Expected booked care_stage 6, got {c_pat_booked[0][0]}"

    # Attempt consultation with empty diagnosis
    st, fail_res = api_call("POST", "/consultations", {
        "appointment_id": app_c_id,
        "patient_id": pC_id,
        "clinical_notes": "Valid clinical notes here",
        "diagnosis": "", # Invalid!
        "treatment_plan": "Valid treatment plan"
    }, token=d1_token)
    print(f"HTTP Status: {st}, Detail: {fail_res.get('detail')}")
    assert st == 400, f"Expected 400 Bad Request, got {st}"
    assert "diagnosis is required" in fail_res.get("detail", ""), f"Unexpected detail: {fail_res}"

    # Verify database was NOT mutated:
    # 1. Appointment status must still be CONFIRMED (not COMPLETED)
    opd_c_check = query_db("SELECT status FROM opd_appointments WHERE id = ?", (app_c_id,))
    assert opd_c_check[0][0] == "CONFIRMED", f"Appointment status should remain CONFIRMED, got {opd_c_check[0][0]}"

    # 2. Patient care stage must still be 6 (has not advanced to 8)
    pat_c_check = query_db("SELECT care_stage FROM patients WHERE user_id = ?", (pC_id,))
    assert pat_c_check[0][0] == 6, f"Patient care stage should remain 6, got {pat_c_check[0][0]}"

    # 3. No consultation record created
    cons_c_check = query_db("SELECT COUNT(*) FROM consultations WHERE appointment_id = ?", (app_c_id,))
    assert cons_c_check[0][0] == 0, f"Expected 0 consultations, found {cons_c_check[0][0]}"

    print("PASS: Validation failure strictly preserves DB state (no mutation, care stage remains 6, not 8)")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 11: Direct SQLite Integrity Audit
    # -------------------------------------------------------------------------
    print("\n--- TEST 11: Direct SQLite Schema & Integrity Audit ---")
    # Verify row count and field values for the finalized consultation
    audit_rows = query_db(
        "SELECT id, appointment_id, reference_id, patient_id, doctor_id, hospital_id, status, clinical_notes, diagnosis, treatment_plan, prescription_medicines, investigations_ordered "
        "FROM consultations WHERE appointment_id = ?",
        (app_doc1_id,)
    )
    assert len(audit_rows) == 1, "Expected exactly 1 consultation row"
    row = audit_rows[0]
    print(f"  ✓ ID: {row[0]}")
    print(f"  ✓ Appointment ID: {row[1]}")
    print(f"  ✓ Reference ID: {row[2]}")
    print(f"  ✓ Patient ID: {row[3]}")
    print(f"  ✓ Doctor ID: {row[4]}")
    print(f"  ✓ Hospital ID: {row[5]}")
    print(f"  ✓ Status: {row[6]}")
    print(f"  ✓ Clinical Notes: {row[7][:40]}...")
    print(f"  ✓ Diagnosis: {row[8]}")
    print(f"  ✓ Treatment Plan: {row[9][:40]}...")
    print(f"  ✓ Prescriptions: {row[10]}")
    print(f"  ✓ Investigations: {row[11]}")

    assert row[6] == "COMPLETED"
    assert "Sorbitrate" in str(row[10])
    assert "Echocardiogram" in str(row[11])

    print("PASS: Direct SQLite integrity audit verified complete data fidelity")
    passed_tests += 1

    print("\n=========================================================================")
    print(f"SUMMARY: {passed_tests}/{total_tests} Phase 4.1 Consultation Tests PASSED!")
    print("=========================================================================")

if __name__ == "__main__":
    main()
