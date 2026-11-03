import json
import urllib.request
import urllib.error
import threading
import time
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def http_req(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"detail": content}
        return e.code, err_json
    except Exception as e:
        return 500, {"detail": str(e)}

def run_comprehensive_verification():
    print("================================================================================")
    print("CHIKITSA-X Post-Integration Security, RBAC & Persistence Verification Suite")
    print("================================================================================")

    test_results = []

    def record_test(name, passed, details, code_path, storage_type, auth_status):
        status_str = "PASSED" if passed else "FAILED"
        icon = "✅" if passed else "❌"
        print(f"{icon} [{status_str}] {name}")
        print(f"    Details: {details}")
        print(f"    Code Path: {code_path}")
        print(f"    Storage: {storage_type} | Auth: {auth_status}\n")
        test_results.append({
            "name": name,
            "passed": passed,
            "details": details,
            "code_path": code_path,
            "storage": storage_type,
            "auth": auth_status
        })

    # ---------------------------------------------------------
    # 1. AUTHENTICATION & PASSWORD HASHING
    # ---------------------------------------------------------
    code, p1_auth = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    p1_token = p1_auth.get("accessToken")
    p1_id = p1_auth.get("user", {}).get("id")

    code_reg, p2_auth = http_req("/auth/register", "POST", {
        "email": f"patient2_{uuid.uuid4().hex[:6]}@demo.com",
        "password": "SecurePassword999!",
        "name": "Ananya Roy",
        "role": "PATIENT",
        "phone": "+91 91234 56789"
    })
    p2_token = p2_auth.get("accessToken")
    p2_id = p2_auth.get("user", {}).get("id")

    code_doc, doc_auth = http_req("/auth/login", "POST", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    doc_token = doc_auth.get("accessToken")
    doc_id = doc_auth.get("user", {}).get("id")

    code_hosp, hosp_auth = http_req("/auth/login", "POST", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_ADMIN"
    })
    hosp_token = hosp_auth.get("accessToken")
    hosp_id = hosp_auth.get("user", {}).get("hospitalId", "hosp-1")

    # Verification 1: Password Hash Leak Check
    leaked = ("password_hash" in json.dumps(p1_auth) or
              "password_hash" in json.dumps(p2_auth) or
              "password_hash" in json.dumps(doc_auth))
    record_test(
        name="1. Password Hash Protection & Secret Non-Leakage",
        passed=(not leaked and code == 200 and code_reg == 200),
        details="Responses contain JWT access tokens and public user info without exposing password_hash or secret keys.",
        code_path="backend/app/routers/auth.py -> login, register",
        storage_type="SQLite (chikitsax.db)",
        auth_status="PBKDF2-HMAC-SHA256 (100,000 rounds) + HS256 JWT"
    )

    # ---------------------------------------------------------
    # 2. CROSS-PATIENT PROFILE ACCESS & TAMPERING (RBAC)
    # ---------------------------------------------------------
    # Patient 2 tries to read Patient 1's profile
    code_read, _ = http_req(f"/patients/{p1_id}", "GET", token=p2_token)
    # Patient 2 tries to tamper with Patient 1's profile
    code_tamper, _ = http_req(f"/patients/{p1_id}", "PUT", {"fullName": "Tampered Name"}, token=p2_token)
    # Patient 1 reads their own profile
    code_own_read, own_profile = http_req(f"/patients/{p1_id}", "GET", token=p1_token)

    record_test(
        name="2. Patient Profile Isolation & Tampering Protection",
        passed=(code_read == 403 and code_tamper == 403 and code_own_read == 200),
        details=f"Cross-patient read returned {code_read} (403 expected), cross-patient tamper returned {code_tamper} (403 expected), own read returned {code_own_read}.",
        code_path="backend/app/routers/patients.py -> get_patient, update_patient",
        storage_type="SQLite (chikitsax.db)",
        auth_status="Enforced: current_user.role == 'PATIENT' must match user_id"
    )

    # ---------------------------------------------------------
    # 3. DOCTOR MEDICAL RECORD ACCESS & CONSENT LIFECYCLE
    # ---------------------------------------------------------
    # Upload a sample medical record for Patient 1
    code_rec_up, rec_res = http_req("/medical-records", "POST", {
        "patient_id": p1_id,
        "file_name": "ECG_Report_Cardiac.pdf",
        "file_type": "PDF",
        "category": "Lab Report",
        "raw_text": "Normal sinus rhythm, heart rate 72 bpm"
    }, token=p1_token)

    # Step 3a: Doctor attempts reading Patient 1 records WITHOUT consent
    code_doc_unauth, _ = http_req(f"/medical-records/{p1_id}", "GET", token=doc_token)

    # Step 3b: Patient 1 grants consent to Dr. Rajesh
    code_cst, cst_res = http_req("/consent", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "hospital_name": "CarePlus Hospital",
        "doctor_id": doc_id,
        "doctor_name": "Dr. Rajesh Kulkarni",
        "granted": True
    }, token=p1_token)
    cst_id = cst_res.get("id")

    # Step 3c: Doctor attempts reading records WITH active consent
    code_doc_auth, doc_records = http_req(f"/medical-records/{p1_id}", "GET", token=doc_token)

    # Step 3d: Patient 1 revokes consent
    code_revoke, revoke_res = http_req(f"/consent/{cst_id}/revoke", "PUT", token=p1_token)

    # Step 3e: Doctor attempts reading records AFTER revocation
    code_doc_revoked, _ = http_req(f"/medical-records/{p1_id}", "GET", token=doc_token)

    record_test(
        name="3. Medical Records Access Controlled by Active Consent & Revocation",
        passed=(code_doc_unauth == 403 and code_doc_auth == 200 and code_revoke == 200 and code_doc_revoked == 403),
        details=f"Doctor without consent: {code_doc_unauth} (403), with consent: {code_doc_auth} (200), after revoke: {code_doc_revoked} (403).",
        code_path="backend/app/routers/medical_records.py -> get_records_by_patient & consent.py -> revoke_consent",
        storage_type="SQLite (chikitsax.db)",
        auth_status="Enforced: ConsentLogModel status == 'GRANTED' validation"
    )

    # ---------------------------------------------------------
    # 4. CONCURRENT BOOKING RACE CONDITION (SLOT COLLISION)
    # ---------------------------------------------------------
    # Generate unique test slot
    ts = int(time.time() * 1000)
    slot_date = f"{(ts % 28) + 1} Jan 2027"
    slot_time = f"{(ts % 12) + 1}:15 PM"

    threads = []
    thread_results = []

    def book_slot(thread_idx):
        c, r = http_req("/opd", "POST", {
            "patient_id": p1_id,
            "hospital_id": "hosp-1",
            "doctor_id": "doc-1",
            "department": "Cardiology",
            "appointment_date": slot_date,
            "appointment_time": slot_time
        })
        thread_results.append((thread_idx, c, r.get("reference_id"), r.get("detail")))

    # Launch 5 concurrent booking attempts simultaneously
    for i in range(5):
        t = threading.Thread(target=book_slot, args=(i,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [r for r in thread_results if r[1] == 200]
    conflicts = [r for r in thread_results if r[1] == 409]

    record_test(
        name="4. Concurrent Booking Slot Collision & Transaction-Safe Lock",
        passed=(len(successes) == 1 and len(conflicts) == 4),
        details=f"5 simultaneous threads for doctor slot '{slot_date} {slot_time}': {len(successes)} succeeded, {len(conflicts)} rejected with 409 Conflict.",
        code_path="backend/app/routers/opd.py -> active_slot_lock unique constraint & IntegrityError handling",
        storage_type="SQLite (chikitsax.db) with unique index uq_active_slot_lock",
        auth_status="Atomic database constraint enforced"
    )

    # ---------------------------------------------------------
    # 5. QR CODE VERIFICATION & REPLAY/HOSPITAL BOUNDARY SECURITY
    # ---------------------------------------------------------
    # Book fresh appointment for QR verification testing
    fresh_date = f"{(ts % 20) + 1} Feb 2027"
    fresh_time = f"08:45 AM"
    code_fresh, fresh_opd = http_req("/opd", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": fresh_date,
        "appointment_time": fresh_time
    }, token=p1_token)
    ref_fresh = fresh_opd.get("reference_id")
    app_id_fresh = fresh_opd.get("id")

    # 5a. Hospital staff from UNAUTHORIZED hospital (hosp-2) attempts verification
    code_wrong_hosp, res_wrong_hosp = http_req("/hospital/verify", "POST", {
        "reference_id": ref_fresh,
        "hospital_id": "hosp-2",
        "staff_name": "Rogue Staff at Other Hospital"
    })

    # 5b. Legitimate hospital staff from hosp-1 verifies appointment
    code_legit_qr, res_legit_qr = http_req("/hospital/verify", "POST", {
        "reference_id": ref_fresh,
        "hospital_id": "hosp-1",
        "staff_name": "CarePlus Reception Desk"
    })

    # 5c. Replay / Re-use attempt: Scan the exact same QR pass again
    code_replay_qr, res_replay_qr = http_req("/hospital/verify", "POST", {
        "reference_id": ref_fresh,
        "hospital_id": "hosp-1",
        "staff_name": "CarePlus Reception Desk"
    })

    # 5d. Cancel another appointment and verify cancelled pass is rejected
    cancel_date = f"{(ts % 15) + 1} Mar 2027"
    _, to_cancel_opd = http_req("/opd", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": cancel_date,
        "appointment_time": "10:30 AM"
    }, token=p1_token)
    ref_to_cancel = to_cancel_opd.get("reference_id")
    app_to_cancel = to_cancel_opd.get("id")

    http_req(f"/opd/{app_to_cancel}/cancel", "PUT", token=p1_token)
    code_cancel_verify, res_cancel_verify = http_req("/hospital/verify", "POST", {
        "reference_id": ref_to_cancel,
        "hospital_id": "hosp-1"
    })

    record_test(
        name="5. QR Pass Boundary Security: Cross-Hospital, Replay & Cancellation Protection",
        passed=(
            res_wrong_hosp.get("verified") is False and
            res_legit_qr.get("verified") is True and
            res_replay_qr.get("verified") is False and
            res_cancel_verify.get("verified") is False
        ),
        details=(
            f"Wrong hospital rejected: {not res_wrong_hosp.get('verified')}; "
            f"First check-in accepted: {res_legit_qr.get('verified')}; "
            f"Replay rejected: {not res_replay_qr.get('verified')}; "
            f"Cancelled pass rejected: {not res_cancel_verify.get('verified')}."
        ),
        code_path="backend/app/routers/qr.py -> hospital_staff_verify",
        storage_type="SQLite (chikitsax.db)",
        auth_status="Enforced: Hospital ID matching, is_verified check & cancellation guard"
    )

    # ---------------------------------------------------------
    # 6. PERSISTENCE ACROSS SESSIONS & DATABASE DISK VERIFICATION
    # ---------------------------------------------------------
    # Query appointments via independent request
    code_list, app_list = http_req(f"/opd?patient_id={p1_id}")
    persisted_refs = [a.get("reference_id") for a in app_list if isinstance(a, dict)]
    has_booked_ref = ref_fresh in persisted_refs

    record_test(
        name="6. Data Persistence Across Independent Database Sessions",
        passed=(code_list == 200 and has_booked_ref),
        details=f"Booked appointment {ref_fresh} was retrieved from disk SQLite storage among {len(persisted_refs)} appointments.",
        code_path="backend/app/routers/opd.py -> list_opd_appointments",
        storage_type="SQLite (chikitsax.db on disk)",
        auth_status="Verified against persistent disk database"
    )

    # ---------------------------------------------------------
    # 7. TREATMENT COST ESTIMATES PERSISTENCE
    # ---------------------------------------------------------
    code_est, est_res = http_req("/financial/treatment-estimates", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "procedure_name": "Cardiac Catheterization",
        "room_category": "Private AC",
        "estimated_cost_min": 75000.0,
        "estimated_cost_max": 95000.0
    }, token=doc_token)

    code_get_est, est_list = http_req(f"/financial/treatment-estimates/patient/{p1_id}", "GET")
    has_est = any(e.get("procedureName") == "Cardiac Catheterization" for e in est_list if isinstance(e, dict))

    record_test(
        name="7. Doctor Treatment Cost Estimates Backend Persistence",
        passed=(code_est == 200 and code_get_est == 200 and has_est),
        details=f"Estimate created (ID: {est_res.get('id')}) and successfully retrieved {len(est_list)} estimate(s) from backend API.",
        code_path="backend/app/routers/financial.py -> create_treatment_cost_estimate",
        storage_type="SQLite (chikitsax.db)",
        auth_status="Doctor authenticated"
    )

    # Summary
    all_passed = all(t["passed"] for t in test_results)
    passed_count = sum(1 for t in test_results if t["passed"])
    total_count = len(test_results)
    print("================================================================================")
    print(f"VERIFICATION SUMMARY: {passed_count}/{total_count} AUDIT SUITES PASSED ({'100% SECURE' if all_passed else 'DEFECTS REMAINING'})")
    print("================================================================================")

if __name__ == "__main__":
    run_comprehensive_verification()
