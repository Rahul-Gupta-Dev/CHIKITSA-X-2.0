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
    print("CHIKITSA-X Phase 4.2: Treatment Cost & Financial Assistance Tests")
    print("=========================================================================")

    ts = int(time.time())
    passed_tests = 0
    total_tests = 10

    # --- Setup Actors ---
    # 1. Register Patient A
    pA_email = f"patientA_fin_{ts}@chikitsax.test"
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
    pB_email = f"patientB_fin_{ts}@chikitsax.test"
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
    d2_email = f"doctor2_fin_{ts}@chikitsax.test"
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
    slot_time = f"{(ts % 11) + 1:02d}:{(ts % 40) + 10:02d} AM"
    st, app_res = api_call("POST", "/opd", {
        "patient_id": pA_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": "2027-08-10",
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
    # TEST 1: Authenticated doctor creates a valid estimate for an authorized patient
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Doctor Creates Valid Treatment Cost Estimate ---")
    st, est_res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "hospital_id": "hosp-1",
        "hospital_name": "CarePlus Super Specialty Hospital",
        "procedure_name": "Coronary Angiography & Stenting Evaluation",
        "room_category": "Semi-Private AC Ward",
        "estimated_cost_min": 65000.0,
        "estimated_cost_max": 85000.0,
        "breakdown": {
            "procedureCost": 40000,
            "roomCharges": 15000,
            "investigationCost": 10000,
            "medicationCost": 8000,
            "otherCharges": 2000
        }
    }, token=d1_token)
    print(f"HTTP Status: {st}, Response ID: {est_res.get('id')}")
    assert st == 200, f"Expected 200 OK, got {st}: {est_res}"
    assert est_res["procedureName"] == "Coronary Angiography & Stenting Evaluation"
    assert est_res["estimatedCostRange"]["min"] == 65000.0
    assert est_res["estimatedCostRange"]["max"] == 85000.0
    est_id = est_res["id"]
    print(f"PASS: Treatment Cost Estimate {est_id} created successfully with HTTP 200")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 2: Estimate persists in SQLite and can be retrieved by authorized actors
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: SQLite Persistence & Authorized Retrieval ---")
    db_rows = query_db("SELECT id, patient_id, procedure_name, estimated_cost_range FROM treatment_cost_estimates WHERE id = ?", (est_id,))
    assert len(db_rows) == 1, f"Expected estimate in SQLite, found {len(db_rows)}"
    print(f"  ✓ Persisted row in SQLite: ID={db_rows[0][0]}, procedure={db_rows[0][2]}")

    # Doctor 1 retrieves estimates for Patient A
    st, doc_list = api_call("GET", f"/financial/treatment-estimates/patient/{pA_id}", token=d1_token)
    assert st == 200, f"Doctor retrieval failed: {doc_list}"
    assert any(e["id"] == est_id for e in doc_list)
    print(f"  ✓ Assigned Doctor retrieved {len(doc_list)} estimate(s) for patient")

    # Patient A retrieves their own estimates
    st, pat_list = api_call("GET", f"/financial/treatment-estimates/patient/{pA_id}", token=pA_token)
    assert st == 200, f"Patient retrieval failed: {pat_list}"
    assert any(e["id"] == est_id for e in pat_list)
    print(f"  ✓ Patient A retrieved their own estimate via /treatment-estimates/patient/{pA_id}")
    print("PASS: Estimate persistence and authorized retrieval verified")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 3: Invalid and negative cost amounts are rejected (HTTP 400)
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Cost Validation & Negative Amount Rejection ---")
    # Negative min cost
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "Test Procedure",
        "estimated_cost_min": -5000.0,
        "estimated_cost_max": 20000.0
    }, token=d1_token)
    assert st == 400, f"Expected 400 for negative min cost, got {st}"
    assert "cannot be negative" in res.get("detail", "")

    # Inverted range (max < min)
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "Test Procedure",
        "estimated_cost_min": 50000.0,
        "estimated_cost_max": 20000.0
    }, token=d1_token)
    assert st == 400, f"Expected 400 for inverted range, got {st}"
    assert "less than" in res.get("detail", "")

    # Negative breakdown item
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "Test Procedure",
        "estimated_cost_min": 10000.0,
        "estimated_cost_max": 20000.0,
        "breakdown": {"bedCharges": -200}
    }, token=d1_token)
    assert st == 400, f"Expected 400 for negative breakdown item, got {st}"
    assert "cannot be negative" in res.get("detail", "")

    # Empty procedure name
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "   ",
        "estimated_cost_min": 10000.0,
        "estimated_cost_max": 20000.0
    }, token=d1_token)
    assert st == 400, f"Expected 400 for empty procedure name, got {st}"
    print("PASS: Negative costs, inverted ranges, and empty procedures rejected with HTTP 400")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 4: IDOR Protection: Patient B cannot access or modify Patient A's financial data
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: IDOR Isolation Across Patients ---")
    # Patient B attempts to get Patient A's estimates
    st, res = api_call("GET", f"/financial/treatment-estimates/patient/{pA_id}", token=pB_token)
    print(f"Patient B reading Patient A estimates -> Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 Forbidden, got {st}"

    # Patient B attempts to get Patient A's insurance policies
    st, res = api_call("GET", f"/financial/insurance/{pA_id}", token=pB_token)
    print(f"Patient B reading Patient A insurance -> Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 Forbidden, got {st}"

    # Patient B attempts to get Patient A's saved assessments
    st, res = api_call("GET", f"/financial/assessments/patient/{pA_id}", token=pB_token)
    print(f"Patient B reading Patient A assessments -> Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 Forbidden, got {st}"

    # Patient B attempts to trigger assessment for Patient A
    st, res = api_call("POST", "/financial/assess", {
        "patient_id": pA_id,
        "treatment_cost": 50000.0
    }, token=pB_token)
    print(f"Patient B running assessment for Patient A -> Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 Forbidden, got {st}"
    print("PASS: Cross-patient access strictly rejected with HTTP 403 Forbidden")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 5: Anonymous and Unauthorized Roles Blocked
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Unauthenticated & Role Authorization Enforcement ---")
    # Unauthenticated create estimate
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "Anon Procedure",
        "estimated_cost_min": 10000.0,
        "estimated_cost_max": 20000.0
    })
    assert st == 401, f"Expected 401 for anonymous request, got {st}"

    # Unauthenticated read estimates
    st, res = api_call("GET", f"/financial/treatment-estimates/patient/{pA_id}")
    assert st == 401, f"Expected 401 for anonymous read, got {st}"

    # Patient role cannot create treatment estimate
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "Self Procedure",
        "estimated_cost_min": 10000.0,
        "estimated_cost_max": 20000.0
    }, token=pA_token)
    assert st == 403, f"Expected 403 for patient role creating estimate, got {st}"
    assert "Patients cannot create" in res.get("detail", "")
    print("PASS: Unauthenticated requests return 401 and patient role creation returns 403")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 6: Doctor cannot create estimate for an unauthorized patient
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Doctor Authorization Gate ---")
    # Doctor 2 (Dr. Ananya Roy) has no appointment or consent with Patient A
    st, res = api_call("POST", "/financial/treatment-estimates", {
        "patient_id": pA_id,
        "procedure_name": "Unauthorized Estimate",
        "estimated_cost_min": 30000.0,
        "estimated_cost_max": 40000.0
    }, token=d2_token)
    print(f"Doctor 2 attempting estimate for Patient A -> Status: {st}, Detail: {res.get('detail')}")
    assert st == 403, f"Expected 403 for unassigned doctor, got {st}"
    assert "not authorized to create treatment estimates" in res.get("detail", "")

    # Doctor 2 also blocked from reading Patient A's estimates
    st, res = api_call("GET", f"/financial/treatment-estimates/patient/{pA_id}", token=d2_token)
    assert st == 403, f"Expected 403 for unassigned doctor read, got {st}"
    print("PASS: Unassigned doctor without appointment or consent blocked with HTTP 403")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 7: Patient Financial Assessment Uses Actual Submitted Form Inputs
    # -------------------------------------------------------------------------
    print("\n--- TEST 7: Financial Assessment Uses Real Submitted Form Inputs ---")
    # Patient A submits custom financial inputs:
    # Cost: 150000, Insurance: 50000, Gov: 40000, NGO: 20000, Self: 20000
    # Expected gap: 150000 - 130000 = 20000
    st, ass_res = api_call("POST", "/financial/assess", {
        "patient_id": pA_id,
        "treatment_cost": 150000.0,
        "hospital_name": "CarePlus Super Specialty Hospital",
        "insurance_coverage": 50000.0,
        "government_support": 40000.0,
        "ngo_assistance": 20000.0,
        "patient_self_contribution": 20000.0
    }, token=pA_token)
    print(f"HTTP Status: {st}, Gap Result: {ass_res.get('estimated_patient_gap')}")
    assert st == 200, f"Assessment failed: {ass_res}"
    assert ass_res["estimated_treatment_cost"] == 150000.0
    assert ass_res["insurance_support"] == 50000.0
    assert ass_res["government_support"] == 40000.0
    assert ass_res["ngo_support"] == 20000.0
    assert ass_res["patient_self_contribution"] == 20000.0
    assert ass_res["estimated_patient_gap"] == 20000.0
    assert ass_res["is_funding_complete"] is False
    ass_id = ass_res["id"]

    # Test 100% funded scenario
    st, full_res = api_call("POST", "/financial/assess", {
        "patient_id": pA_id,
        "treatment_cost": 100000.0,
        "insurance_coverage": 60000.0,
        "government_support": 30000.0,
        "ngo_assistance": 10000.0,
        "patient_self_contribution": 0.0
    }, token=pA_token)
    assert st == 200
    assert full_res["estimated_patient_gap"] == 0.0
    assert full_res["is_funding_complete"] is True
    print("PASS: Financial assessment calculates exactly against real submitted form inputs")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 8: Financial Plan Validation and Persistence in SQLite
    # -------------------------------------------------------------------------
    print("\n--- TEST 8: SQLite Assessment Persistence & Care Stage Advance ---")
    # Verify assessment persisted in SQLite care_to_cost_assessments table
    ass_rows = query_db("SELECT id, patient_id, estimated_treatment_cost, financial_gap, is_funding_complete FROM care_to_cost_assessments WHERE id = ?", (ass_id,))
    assert len(ass_rows) == 1, f"Assessment {ass_id} not found in SQLite"
    print(f"  ✓ Persisted assessment in DB: ID={ass_rows[0][0]}, cost={ass_rows[0][2]}, gap={ass_rows[0][3]}")

    # Patient A retrieves their saved assessments
    st, my_ass = api_call("GET", f"/financial/assessments/patient/{pA_id}", token=pA_token)
    assert st == 200, f"Retrieving assessments failed: {my_ass}"
    assert any(a["id"] == ass_id for a in my_ass)
    print(f"  ✓ Patient A retrieved {len(my_ass)} saved assessment(s) from SQLite")

    # Verify patient care_stage in SQLite advanced to 11
    pat_rows = query_db("SELECT care_stage FROM patients WHERE user_id = ? OR id = ?", (pA_id, pA_id))
    assert len(pat_rows) >= 1
    assert pat_rows[0][0] == 11, f"Expected patient care_stage == 11, got {pat_rows[0][0]}"
    print(f"  ✓ Patient care_stage advanced to: {pat_rows[0][0]}")

    # Test /financial/finance-plan calculation and negative rejection
    st, plan_res = api_call("POST", "/financial/finance-plan", {
        "treatment_cost": 120000.0,
        "insurance_coverage": 60000.0,
        "government_support": 30000.0,
        "ngo_support": 15000.0,
        "additional_savings": 15000.0
    }, token=pA_token)
    assert st == 200
    assert plan_res["remaining_gap"] == 0.0
    assert "ZERO OUT-OF-POCKET GAP" in plan_res["recommendation_tag"]

    # Negative amount in finance plan rejected
    st, neg_plan = api_call("POST", "/financial/finance-plan", {
        "treatment_cost": -500.0
    }, token=pA_token)
    assert st == 400
    print("PASS: Assessment persisted, care stage advanced to 11, and finance plan verified")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 9: Informational Directory Listings and Disclaimers
    # -------------------------------------------------------------------------
    print("\n--- TEST 9: Informational Directory Listings & Clear Disclosures ---")
    st, schemes = api_call("GET", f"/financial/schemes/{pA_id}", token=pA_token)
    assert st == 200
    assert len(schemes) >= 2
    assert any(s["schemeCode"] == "PM-JAY" for s in schemes)
    print(f"  ✓ Retrieved {len(schemes)} Government Schemes from DB")

    st, ngos = api_call("GET", f"/financial/ngo-support/{pA_id}", token=pA_token)
    assert st == 200
    assert len(ngos) >= 2
    assert any("Tata Trusts" in n["organizationName"] for n in ngos)
    print(f"  ✓ Retrieved {len(ngos)} NGO Support listings from DB")

    assert "disclaimer" in ass_res
    assert "Indicative" in ass_res["disclaimer"]
    print("PASS: Directory listings and required informational disclosures verified")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 10: Direct SQLite Database Integrity & Field Verification
    # -------------------------------------------------------------------------
    print("\n--- TEST 10: Direct SQLite Integrity Audit ---")
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # Verify treatment_cost_estimates columns
        cur.execute("SELECT id, hospital_name, procedure_name, room_category, estimated_cost_range, breakdown FROM treatment_cost_estimates WHERE id = ?", (est_id,))
        row = cur.fetchone()
        assert row is not None
        assert row[1] == "CarePlus Super Specialty Hospital"
        assert row[2] == "Coronary Angiography & Stenting Evaluation"
        assert "min" in str(row[4])
        assert "procedureCost" in str(row[5])
        print("  ✓ treatment_cost_estimates record verified with complete JSON breakdown and tariffs")

        # Verify care_to_cost_assessments columns
        cur.execute("SELECT id, hospital_name, estimated_treatment_cost, insurance_coverage, government_support, financial_gap FROM care_to_cost_assessments WHERE id = ?", (ass_id,))
        a_row = cur.fetchone()
        assert a_row is not None
        assert a_row[2] == 150000.0
        assert a_row[3] == 50000.0
        assert a_row[4] == 40000.0
        assert a_row[5] == 20000.0
        print("  ✓ care_to_cost_assessments record verified with exact numeric precision")
    finally:
        conn.close()

    print("PASS: Direct SQLite integrity audit confirmed 100% data fidelity")
    passed_tests += 1

    print("\n=========================================================================")
    print(f"SUMMARY: {passed_tests}/{total_tests} Phase 4.2 Financial Tests PASSED!")
    print("=========================================================================")

if __name__ == "__main__":
    main()
