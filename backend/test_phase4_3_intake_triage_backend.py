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
    print("CHIKITSA-X Phase 4.3: Secure Clinical Intake & Triage Backend Tests")
    print("=========================================================================")

    ts = int(time.time())
    passed_tests = 0
    total_tests = 10

    # --- Setup Actors ---
    # 1. Register Patient A
    pA_email = f"patientA_tri_{ts}@chikitsax.test"
    st, reg_res = api_call("POST", "/auth/register", {
        "name": f"Aarav Sharma {ts}",
        "fullName": f"Aarav Sharma {ts}",
        "email": pA_email,
        "phone": "+91 97111 22222",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200, f"Registration of Patient A failed: {reg_res}"
    pA_token = reg_res["accessToken"]
    pA_id = reg_res["user"]["id"]

    # 2. Register Patient B (Unauthorized for Patient A's records)
    pB_email = f"patientB_tri_{ts}@chikitsax.test"
    st, reg_res_b = api_call("POST", "/auth/register", {
        "name": f"Meera Iyer {ts}",
        "fullName": f"Meera Iyer {ts}",
        "email": pB_email,
        "phone": "+91 97222 33333",
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

    # 4. Register Doctor 2 (Dr. Ananya Roy - unassigned to Patient A) via authorized Hospital Admin
    d2_email = f"doctor2_tri_{ts}@chikitsax.test"
    st, reg_res_d2 = api_call("POST", "/auth/register", {
        "name": "Dr. Ananya Roy",
        "fullName": "Dr. Ananya Roy",
        "email": d2_email,
        "phone": "+91 97333 44444",
        "password": "Password123!",
        "role": "DOCTOR",
        "hospitalId": "hosp-1"
    }, token=h_token)
    assert st == 200, f"Registration of Doctor 2 failed: {reg_res_d2}"
    d2_token = reg_res_d2["accessToken"]
    d2_id = reg_res_d2["user"]["id"]

    # Patient A books an OPD Appointment with Doctor 1 (Dr. Rajesh Kulkarni)
    slot_day = f"{(ts % 20) + 1:02d}"
    slot_time = f"{(ts % 11) + 1:02d}:{(ts % 40) + 10:02d} AM"
    st, app_res = api_call("POST", "/opd", {
        "patient_id": pA_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": f"2027-09-{slot_day}",
        "appointment_time": slot_time
    }, token=pA_token)
    assert st == 200, f"OPD booking failed: {app_res}"
    app_id = app_res["id"]

    print("Actors setup complete:")
    print(f"  - Patient A: {pA_id} (Has appointment {app_id} with Dr. Rajesh)")
    print(f"  - Patient B: {pB_id} (Unrelated patient)")
    print(f"  - Doctor 1 (Assigned): {d1_id} (Dr. Rajesh Kulkarni)")
    print(f"  - Doctor 2 (Unassigned): {d2_id} (Dr. Ananya Roy)")

    # -------------------------------------------------------------------------
    # TEST 1: Unauthenticated intake and triage requests return 401
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Unauthenticated Access Enforcement (401 Unauthorized) ---")
    st1, res1 = api_call("POST", "/intake", {"transcript": "Feeling dizzy and weak"})
    assert st1 == 401, f"Expected 401 for unauthenticated intake POST, got {st1}: {res1}"

    st2, res2 = api_call("GET", f"/intake/patient/{pA_id}")
    assert st2 == 401, f"Expected 401 for unauthenticated intake GET, got {st2}: {res2}"

    st3, res3 = api_call("POST", "/triage", {"patient_id": pA_id})
    assert st3 == 401, f"Expected 401 for unauthenticated triage POST, got {st3}: {res3}"

    st4, res4 = api_call("GET", f"/triage/patient/{pA_id}")
    assert st4 == 401, f"Expected 401 for unauthenticated triage GET, got {st4}: {res4}"

    passed_tests += 1
    print("✓ PASS: All unauthenticated intake and triage endpoints return 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # TEST 2: Authenticated patient submits valid intake and persists in SQLite
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Patient Submits Valid Intake and Persists in SQLite ---")
    st, intake_res = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": "I have mild sore throat and dry cough for two days",
        "duration": "2 Days",
        "severity": "Mild"
    }, token=pA_token)
    assert st == 200, f"Intake submission failed: {intake_res}"
    assert "id" in intake_res, "Missing id in intake response"
    assert intake_res["patient_id"] == pA_id, "Patient ID mismatch in intake response"
    assert "Sore Throat & Cough" in intake_res["extracted_symptoms"], f"Expected symptom extraction, got: {intake_res['extracted_symptoms']}"
    intake_a_id = intake_res["id"]

    # Verify SQLite row
    db_intake = query_db("SELECT id, patient_id, raw_transcript, severity FROM intake_sessions WHERE id = ?", (intake_a_id,))
    assert len(db_intake) == 1, f"Intake row not found in SQLite: {db_intake}"
    assert db_intake[0][1] == pA_id, "SQLite patient_id mismatch"
    assert "sore throat" in db_intake[0][2].lower(), "SQLite raw_transcript mismatch"

    passed_tests += 1
    print(f"✓ PASS: Intake {intake_a_id} created and verified in SQLite database.")

    # -------------------------------------------------------------------------
    # TEST 3: Patient cannot submit or read intake/triage for another patient (403 IDOR)
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: IDOR Prevention: Cross-Patient Submissions & Reads (403 Forbidden) ---")
    # Patient B attempts to submit intake for Patient A
    st, res = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": "Attempted cross-patient intake spoofing"
    }, token=pB_token)
    assert st == 403, f"Expected 403 when Patient B submits intake for Patient A, got {st}: {res}"

    # Patient B attempts to read Patient A's intakes
    st, res = api_call("GET", f"/intake/patient/{pA_id}", token=pB_token)
    assert st == 403, f"Expected 403 when Patient B reads Patient A's intakes, got {st}: {res}"

    # Patient B attempts to triage Patient A
    st, res = api_call("POST", "/triage", {
        "patient_id": pA_id
    }, token=pB_token)
    assert st == 403, f"Expected 403 when Patient B triages Patient A, got {st}: {res}"

    # Patient B attempts to read Patient A's triage records
    st, res = api_call("GET", f"/triage/patient/{pA_id}", token=pB_token)
    assert st == 403, f"Expected 403 when Patient B reads Patient A's triages, got {st}: {res}"

    passed_tests += 1
    print("✓ PASS: IDOR attacks between patients are strictly rejected with 403 Forbidden.")

    # -------------------------------------------------------------------------
    # TEST 4: Doctor Authorization Enforced (Unassigned doctor rejected with 403)
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Doctor Clinical Authorization Check (403 Forbidden) ---")
    # Unassigned Doctor 2 attempts to submit intake for Patient A
    st, res = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": "Unassigned doctor attempting clinical intake"
    }, token=d2_token)
    assert st == 403, f"Expected 403 for unassigned doctor intake, got {st}: {res}"

    # Unassigned Doctor 2 attempts to view Patient A's intakes
    st, res = api_call("GET", f"/intake/patient/{pA_id}", token=d2_token)
    assert st == 403, f"Expected 403 for unassigned doctor view intake, got {st}: {res}"

    # Unassigned Doctor 2 attempts to triage Patient A
    st, res = api_call("POST", "/triage", {
        "patient_id": pA_id
    }, token=d2_token)
    assert st == 403, f"Expected 403 for unassigned doctor triage, got {st}: {res}"

    # Assigned Doctor 1 CAN access Patient A's intakes
    st, d1_view = api_call("GET", f"/intake/patient/{pA_id}", token=d1_token)
    assert st == 200, f"Assigned doctor failed to view patient intakes: {d1_view}"
    assert isinstance(d1_view, list) and len(d1_view) >= 1, "Assigned doctor did not receive patient intakes"

    passed_tests += 1
    print("✓ PASS: Unassigned doctor rejected with 403; assigned doctor successfully authorized.")

    # -------------------------------------------------------------------------
    # TEST 5: Valid triage produces structured evaluation and persists in SQLite
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Structured Clinical Triage Evaluation & Persistence ---")
    st, triage_res = api_call("POST", "/triage", {
        "patient_id": pA_id,
        "intake_id": intake_a_id
    }, token=pA_token)
    assert st == 200, f"Clinical triage failed: {triage_res}"
    assert "id" in triage_res, "Missing id in triage response"
    assert triage_res["risk_level"] in ["LOW", "MODERATE", "HIGH"], f"Invalid risk level: {triage_res['risk_level']}"
    assert "urgency" in triage_res, "Missing urgency"
    assert "disclaimer" in triage_res, "Missing medical disclaimer"
    assert "AI-assisted" in triage_res["disclaimer"], "Disclaimer missing AI-assisted notice"
    triage_a_id = triage_res["id"]

    # Verify SQLite row
    db_triage = query_db("SELECT id, patient_id, risk_level, urgency FROM triage_results WHERE id = ?", (triage_a_id,))
    assert len(db_triage) == 1, f"Triage row not found in SQLite: {db_triage}"
    assert db_triage[0][1] == pA_id, "SQLite patient_id mismatch"

    # Patient reads their own triage records
    st, list_triage = api_call("GET", f"/triage/patient/{pA_id}", token=pA_token)
    assert st == 200, f"Failed to list triage results: {list_triage}"
    assert any(t["id"] == triage_a_id for t in list_triage), "Created triage not in list"

    passed_tests += 1
    print(f"✓ PASS: Triage {triage_a_id} successfully evaluated, persisted, and retrieved.")

    # -------------------------------------------------------------------------
    # TEST 6: Input validation: empty transcript (400) and oversized input (422)
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Input Validation: Empty (400) and Oversized >5000 chars (422) ---")
    # Empty transcript
    st, res = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": ""
    }, token=pA_token)
    assert st == 400, f"Expected 400 for empty transcript, got {st}: {res}"

    # Whitespace-only transcript
    st, res = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": "     "
    }, token=pA_token)
    assert st == 400, f"Expected 400 for whitespace transcript, got {st}: {res}"

    # Oversized transcript (>5000 chars)
    giant_text = "I have a headache. " * 300  # ~5700 chars
    st, res = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": giant_text
    }, token=pA_token)
    assert st == 422, f"Expected 422 for transcript > 5000 chars, got {st}: {res}"

    passed_tests += 1
    print("✓ PASS: Empty input rejected with 400; oversized input rejected with 422.")

    # -------------------------------------------------------------------------
    # TEST 7: Intake session mismatch (400) and non-existent intake (404) on triage
    # -------------------------------------------------------------------------
    print("\n--- TEST 7: Intake Session Mismatch (400) and Non-Existent Intake (404) ---")
    # Patient B creates an intake session
    st, intake_b_res = api_call("POST", "/intake", {
        "patient_id": pB_id,
        "transcript": "Abdominal pain and mild nausea since morning"
    }, token=pB_token)
    assert st == 200, f"Patient B intake failed: {intake_b_res}"
    intake_b_id = intake_b_res["id"]

    # Patient A attempts to run triage referencing Patient B's intake
    st, res = api_call("POST", "/triage", {
        "patient_id": pA_id,
        "intake_id": intake_b_id
    }, token=pA_token)
    assert st == 400, f"Expected 400 for cross-patient intake_id mismatch, got {st}: {res}"

    # Patient A attempts to run triage with non-existent intake_id
    st, res = api_call("POST", "/triage", {
        "patient_id": pA_id,
        "intake_id": "intake-non-existent-999999"
    }, token=pA_token)
    assert st == 404, f"Expected 404 for non-existent intake_id, got {st}: {res}"

    passed_tests += 1
    print("✓ PASS: Conflicting intake session rejected with 400; non-existent intake rejected with 404.")

    # -------------------------------------------------------------------------
    # TEST 8: NLP Symptom extraction & Care stage progression (care_stage >= 2)
    # -------------------------------------------------------------------------
    print("\n--- TEST 8: NLP Symptom Extraction & Care Stage Progression ---")
    st, intake_nlp = api_call("POST", "/intake", {
        "patient_id": pA_id,
        "transcript": "Severe fever and chills since yesterday, feeling headache and dizziness"
    }, token=pA_token)
    assert st == 200, f"NLP intake failed: {intake_nlp}"
    symptoms = intake_nlp["extracted_symptoms"]
    assert any("Fever" in s for s in symptoms), f"Expected fever in symptoms: {symptoms}"
    assert any("Headache" in s for s in symptoms), f"Expected headache in symptoms: {symptoms}"
    assert any("Dizziness" in s for s in symptoms), f"Expected dizziness in symptoms: {symptoms}"

    # Verify PatientModel care_stage in SQLite
    db_patient = query_db("SELECT care_stage, symptoms FROM patients WHERE user_id = ? OR id = ?", (pA_id, pA_id))
    assert len(db_patient) >= 1, f"Patient row not found: {db_patient}"
    care_stage = db_patient[0][0]
    assert care_stage >= 2, f"Expected patient care_stage >= 2 after intake, got {care_stage}"

    passed_tests += 1
    print(f"✓ PASS: Multiple symptoms accurately extracted; care_stage progressed to {care_stage}.")

    # -------------------------------------------------------------------------
    # TEST 9: Severe red-flag emergency detection and high-urgency guidance
    # -------------------------------------------------------------------------
    print("\n--- TEST 9: Emergency Red-Flag Detection & Critical Triage Routing ---")
    # Register new patient C to test emergency workflow cleanly
    pC_email = f"patientC_emerg_{ts}@chikitsax.test"
    st, reg_res_c = api_call("POST", "/auth/register", {
        "name": f"Vikram Sen {ts}",
        "fullName": f"Vikram Sen {ts}",
        "email": pC_email,
        "phone": "+91 97444 55555",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200, f"Registration of Patient C failed: {reg_res_c}"
    pC_token = reg_res_c["accessToken"]
    pC_id = reg_res_c["user"]["id"]

    # Submit emergency intake with cardiorespiratory red flags
    st, emerg_intake = api_call("POST", "/intake", {
        "patient_id": pC_id,
        "transcript": "Severe crushing chest pain and shortness of breath with sweating and dizziness"
    }, token=pC_token)
    assert st == 200, f"Emergency intake failed: {emerg_intake}"
    assert emerg_intake["is_emergency_alert"] is True, f"Expected emergency alert True, got {emerg_intake}"
    assert emerg_intake["severity"] == "Severe", f"Expected severity Severe, got {emerg_intake['severity']}"

    # Evaluate triage for emergency intake
    st, emerg_triage = api_call("POST", "/triage", {
        "patient_id": pC_id,
        "intake_id": emerg_intake["id"]
    }, token=pC_token)
    assert st == 200, f"Emergency triage failed: {emerg_triage}"
    assert emerg_triage["risk_level"] == "HIGH", f"Expected risk_level HIGH, got {emerg_triage['risk_level']}"
    assert emerg_triage["is_emergency_triggered"] is True, "Expected is_emergency_triggered True"
    assert "Urgent" in emerg_triage["urgency"] or "Immediate" in emerg_triage["urgency"], f"Expected urgent guidance, got: {emerg_triage['urgency']}"

    # Check that patient care_stage progressed to 4
    db_patient_c = query_db("SELECT care_stage FROM patients WHERE user_id = ? OR id = ?", (pC_id, pC_id))
    assert len(db_patient_c) >= 1, "Patient C row not found"
    assert db_patient_c[0][0] >= 4, f"Expected care_stage >= 4 after triage, got {db_patient_c[0][0]}"

    passed_tests += 1
    print("✓ PASS: Critical red-flags correctly triggered emergency alert and HIGH triage risk level.")

    # -------------------------------------------------------------------------
    # TEST 10: Direct SQLite Database Verification & Schema Audit
    # -------------------------------------------------------------------------
    print("\n--- TEST 10: Direct SQLite Database Verification & Schema Audit ---")
    intake_count = query_db("SELECT COUNT(*) FROM intake_sessions")[0][0]
    triage_count = query_db("SELECT COUNT(*) FROM triage_results")[0][0]
    print(f"  Current SQLite record counts: intake_sessions = {intake_count}, triage_results = {triage_count}")
    assert intake_count >= 3, f"Expected at least 3 intake sessions in SQLite, found {intake_count}"
    assert triage_count >= 2, f"Expected at least 2 triage results in SQLite, found {triage_count}"

    # Verify column structure of both tables
    intake_cols = [col[1] for col in query_db("PRAGMA table_info(intake_sessions)")]
    assert "id" in intake_cols and "patient_id" in intake_cols and "raw_transcript" in intake_cols and "is_emergency_alert" in intake_cols

    triage_cols = [col[1] for col in query_db("PRAGMA table_info(triage_results)")]
    assert "id" in triage_cols and "patient_id" in triage_cols and "risk_level" in triage_cols and "is_emergency_triggered" in triage_cols

    passed_tests += 1
    print("✓ PASS: SQLite persistence, schema, and record count successfully verified.")

    print("\n=========================================================================")
    print(f"RESULTS: {passed_tests}/{total_tests} Phase 4.3 Tests Passed Successfully.")
    print("=========================================================================")

if __name__ == "__main__":
    main()
