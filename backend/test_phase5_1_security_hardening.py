"""
CHIKITSA-X - Phase 5.1 Critical Authentication & API Authorization Hardening Test Suite
Verifies all 14 mandatory security and access control checks.
"""

import sys
import os
import json
import time
import base64
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"

def api_call(method: str, endpoint: str, data=None, token: str = None):
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

def decode_jwt_unverified(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded)
    return json.loads(decoded_bytes.decode("utf-8"))

def run_tests():
    print("================================================================================")
    print("CHIKITSA-X - Phase 5.1 Critical Authentication & Authorization Hardening Tests")
    print("================================================================================")

    results = []

    def record_check(num: int, title: str, passed: bool, msg: str = ""):
        status_str = "PASS" if passed else "FAIL"
        results.append((num, title, status_str, msg))
        icon = "✅" if passed else "❌"
        print(f"{icon} Check {num}: {title} [{status_str}] {('- ' + msg) if msg else ''}")
        if not passed:
            raise AssertionError(f"Check {num} FAILED: {msg}")

    # Baseline authentications
    # Patient 1
    st, p1_login = api_call("POST", "/auth/login", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    assert st == 200, f"Patient login failed: {p1_login}"
    p1_token = p1_login["accessToken"]
    p1_user = p1_login["user"]
    p1_id = p1_user["id"]

    # Doctor 1 (Dr. Rajesh Kulkarni, doc-1 at hosp-1)
    st, d1_login = api_call("POST", "/auth/login", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    assert st == 200, f"Doctor login failed: {d1_login}"
    d1_token = d1_login["accessToken"]

    # Hospital Admin 1 (hosp-1)
    st, h1_login = api_call("POST", "/auth/login", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_ADMIN"
    })
    assert st == 200, f"Hospital login failed: {h1_login}"
    h1_token = h1_login["accessToken"]

    # -------------------------------------------------------------------------
    # Check 1: Login role escalation attempt
    # -------------------------------------------------------------------------
    st_esc_admin, esc_res_admin = api_call("POST", "/auth/login", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_ADMIN"
    })
    st_esc_doc, esc_res_doc = api_call("POST", "/auth/login", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    c1_passed = (st_esc_admin == 403 and st_esc_doc == 403)
    # Also verify legitimate patient login issued token strictly embeds PATIENT role
    p1_jwt = decode_jwt_unverified(p1_token)
    assert p1_jwt.get("role") == "PATIENT", "JWT role is not PATIENT"
    record_check(1, "Role escalation rejection on login", c1_passed,
                 f"Admin attempt code: {st_esc_admin}, Doc attempt code: {st_esc_doc}")

    # -------------------------------------------------------------------------
    # Check 2: Self-registration with role: 'DOCTOR' without admin authorization returns 403
    # -------------------------------------------------------------------------
    ts = int(time.time() * 1000)
    st_reg_doc, reg_doc_res = api_call("POST", "/auth/register", {
        "email": f"unauth_doc_{ts}@test.com",
        "password": "DocPassword123!",
        "name": "Dr. Unverified Impostor",
        "role": "DOCTOR"
    })
    record_check(2, "Self-registration as DOCTOR without authorization blocked",
                 st_reg_doc == 403, f"Returned status: {st_reg_doc}")

    # -------------------------------------------------------------------------
    # Check 3: Self-registration with role: 'HOSPITAL_ADMIN' without admin authorization returns 403
    # -------------------------------------------------------------------------
    st_reg_admin, reg_admin_res = api_call("POST", "/auth/register", {
        "email": f"unauth_hosp_{ts}@test.com",
        "password": "AdminPassword123!",
        "name": "Fake Hospital Admin",
        "role": "HOSPITAL_ADMIN"
    })
    record_check(3, "Self-registration as HOSPITAL_ADMIN without authorization blocked",
                 st_reg_admin == 403, f"Returned status: {st_reg_admin}")

    # -------------------------------------------------------------------------
    # Check 4: Patient self-registration (role: 'PATIENT' or omitted) succeeds with HTTP 200
    # -------------------------------------------------------------------------
    p_reg_email = f"legit_patient_{ts}@test.com"
    st_reg_pat, reg_pat_res = api_call("POST", "/auth/register", {
        "email": p_reg_email,
        "password": "PatientPassword123!",
        "name": "Legitimate Patient",
        "role": "PATIENT",
        "phone": "+91 98888 77777"
    })
    c4_passed = (st_reg_pat == 200 and "accessToken" in reg_pat_res and reg_pat_res["user"]["role"] == "PATIENT")
    p2_token = reg_pat_res.get("accessToken")
    p2_id = reg_pat_res.get("user", {}).get("id")
    record_check(4, "Patient self-registration succeeds with HTTP 200 and JWT",
                 c4_passed, f"Returned status: {st_reg_pat}")

    # Seed an appointment at hosp-1 for check-in and PII tests
    slot_date = f"{(ts % 25) + 1} Aug 2027"
    slot_time = f"{((ts // 1000) % 12) + 1}:{(ts % 50) + 10:02d} AM"
    st_book, book_res = api_call("POST", "/opd", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": slot_date,
        "appointment_time": slot_time
    }, token=p1_token)
    assert st_book == 200, f"Appointment booking failed: {book_res}"
    ref_id = book_res["reference_id"]
    app_id = book_res["id"]

    # -------------------------------------------------------------------------
    # Check 5: Unauthenticated POST /api/hospital/verify returns HTTP 401
    # -------------------------------------------------------------------------
    st_anon_checkin, _ = api_call("POST", "/hospital/verify", {
        "reference_id": ref_id,
        "hospital_id": "hosp-1"
    })
    record_check(5, "Unauthenticated POST /api/hospital/verify rejected with HTTP 401",
                 st_anon_checkin == 401, f"Returned status: {st_anon_checkin}")

    # -------------------------------------------------------------------------
    # Check 6: Check-in from non-staff role (e.g. PATIENT) returns HTTP 403
    # -------------------------------------------------------------------------
    st_pat_checkin, _ = api_call("POST", "/hospital/verify", {
        "reference_id": ref_id,
        "hospital_id": "hosp-1"
    }, token=p1_token)
    record_check(6, "Check-in by non-staff role (PATIENT) rejected with HTTP 403",
                 st_pat_checkin == 403, f"Returned status: {st_pat_checkin}")

    # -------------------------------------------------------------------------
    # Check 7: Cross-hospital check-in attempt returns HTTP 403
    # -------------------------------------------------------------------------
    # h1_token belongs to hosp-1, sending payload hospital_id="hosp-2" or attempting cross-hospital
    st_cross_checkin, _ = api_call("POST", "/hospital/verify", {
        "reference_id": ref_id,
        "hospital_id": "hosp-2"
    }, token=h1_token)
    record_check(7, "Cross-hospital check-in rejected with HTTP 403",
                 st_cross_checkin == 403, f"Returned status: {st_cross_checkin}")

    # -------------------------------------------------------------------------
    # Check 8: Legitimate hospital check-in by authorized staff succeeds with HTTP 200
    # -------------------------------------------------------------------------
    st_legit_checkin, legit_checkin_res = api_call("POST", "/hospital/verify", {
        "reference_id": ref_id,
        "hospital_id": "hosp-1",
        "staff_name": "Nurse Station A"
    }, token=h1_token)
    c8_passed = (st_legit_checkin == 200 and legit_checkin_res.get("verified") is True and legit_checkin_res.get("status") == "VERIFIED")
    record_check(8, "Authorized staff check-in succeeds with 200 and VERIFIED status",
                 c8_passed, f"Returned status: {st_legit_checkin}, Verified: {legit_checkin_res.get('verified')}")

    # -------------------------------------------------------------------------
    # Check 9: Unauthenticated GET /api/doctors/{doctor_id}/appointments returns HTTP 401
    # -------------------------------------------------------------------------
    st_anon_doc_apps, _ = api_call("GET", "/doctors/doc-1/appointments")
    record_check(9, "Unauthenticated GET /api/doctors/{id}/appointments returns HTTP 401",
                 st_anon_doc_apps == 401, f"Returned status: {st_anon_doc_apps}")

    # -------------------------------------------------------------------------
    # Check 10: Patient accessing another doctor's appointments returns HTTP 403
    # -------------------------------------------------------------------------
    st_pat_doc_apps, _ = api_call("GET", "/doctors/doc-1/appointments", token=p1_token)
    record_check(10, "Patient accessing doctor appointments rejected with HTTP 403",
                 st_pat_doc_apps == 403, f"Returned status: {st_pat_doc_apps}")

    # -------------------------------------------------------------------------
    # Check 11: Authorized doctor accessing own appointments returns HTTP 200
    # -------------------------------------------------------------------------
    st_doc_apps, doc_apps_res = api_call("GET", "/doctors/doc-1/appointments", token=d1_token)
    c11_passed = (st_doc_apps == 200 and isinstance(doc_apps_res, list))
    record_check(11, "Authorized doctor accessing own appointments returns HTTP 200",
                 c11_passed, f"Returned status: {st_doc_apps}, Count: {len(doc_apps_res) if isinstance(doc_apps_res, list) else 0}")

    # -------------------------------------------------------------------------
    # Check 12: Unauthenticated and IDOR access to GET /api/opd/{appointment_id} returns HTTP 401 / 403
    # -------------------------------------------------------------------------
    st_anon_opd, _ = api_call("GET", f"/opd/{app_id}")
    st_idor_opd, _ = api_call("GET", f"/opd/{app_id}", token=p2_token)
    st_owner_opd, owner_res = api_call("GET", f"/opd/{app_id}", token=p1_token)
    st_doc_opd, doc_res = api_call("GET", f"/opd/{app_id}", token=d1_token)
    c12_passed = (st_anon_opd == 401 and st_idor_opd == 403 and st_owner_opd == 200 and st_doc_opd == 200)
    record_check(12, "GET /api/opd/{appointment_id} enforces authentication and patient/doctor authorization",
                 c12_passed, f"Anon: {st_anon_opd}, IDOR: {st_idor_opd}, Owner: {st_owner_opd}, Doc: {st_doc_opd}")

    # -------------------------------------------------------------------------
    # Check 13: Audit logs access control
    # -------------------------------------------------------------------------
    st_anon_audit, _ = api_call("GET", "/audit-logs")
    st_pat_audit, _ = api_call("GET", "/audit-logs", token=p1_token)
    st_doc_audit, _ = api_call("GET", "/audit-logs", token=d1_token)
    st_admin_audit, admin_audit_res = api_call("GET", "/audit-logs", token=h1_token)

    # POST audit log binding check
    st_post_audit_anon, _ = api_call("POST", "/audit-logs", {
        "action": "FORGED_LOG",
        "actor_id": "fake-actor",
        "actor_role": "ADMIN",
        "details": "Tampered log attempt"
    })
    st_post_audit_admin, post_audit_res = api_call("POST", "/audit-logs", {
        "action": "ADMIN_VERIFY",
        "actor_id": "fake-actor-injected",
        "actor_role": "ADMIN_INJECTED",
        "details": "Staff check-in audit"
    }, token=h1_token)

    c13_passed = (
        st_anon_audit == 401 and
        st_pat_audit == 403 and
        st_doc_audit == 403 and
        st_admin_audit == 200 and
        st_post_audit_anon == 401 and
        st_post_audit_admin == 200 and
        post_audit_res.get("actorRole") == "HOSPITAL_ADMIN" and
        post_audit_res.get("actorId") == h1_login["user"]["id"]
    )
    record_check(13, "Audit logs access control and actor binding enforced",
                 c13_passed, f"Anon: {st_anon_audit}, Pat: {st_pat_audit}, Admin: {st_admin_audit}, BoundActor: {post_audit_res.get('actorId')}")

    # -------------------------------------------------------------------------
    # Check 14: POST /api/medical-records and POST /api/patients reject unauthenticated and cross-user
    # -------------------------------------------------------------------------
    # Medical records creation check
    st_med_anon, _ = api_call("POST", "/medical-records", {
        "patient_id": p1_id,
        "file_name": "malicious_report.pdf",
        "file_type": "PDF",
        "category": "Prescription"
    })
    st_med_cross, _ = api_call("POST", "/medical-records", {
        "patient_id": p1_id,
        "file_name": "attacker_injected_report.pdf",
        "file_type": "PDF",
        "category": "Prescription"
    }, token=p2_token)

    # Patient creation check
    st_pat_anon, _ = api_call("POST", "/patients", {
        "userId": p1_id,
        "fullName": "Fake Patient Profile",
        "age": 40,
        "gender": "Female",
        "bloodGroup": "A+",
        "phone": "+91 99999 11111",
        "email": "fakepatient@test.com",
        "address": "123 Street",
        "city": "Delhi",
        "pincode": "110001"
    })
    st_pat_cross, _ = api_call("POST", "/patients", {
        "userId": p1_id,
        "fullName": "Attacker Hijack Profile",
        "age": 40,
        "gender": "Female",
        "bloodGroup": "A+",
        "phone": "+91 99999 11111",
        "email": "fakepatient@test.com",
        "address": "123 Street",
        "city": "Delhi",
        "pincode": "110001"
    }, token=p2_token)

    c14_passed = (
        st_med_anon == 401 and
        st_med_cross == 403 and
        st_pat_anon == 401 and
        st_pat_cross == 403
    )
    record_check(14, "Medical-record & Patient creation endpoints reject 401 unauthenticated and 403 cross-user",
                 c14_passed, f"MedAnon: {st_med_anon}, MedCross: {st_med_cross}, PatAnon: {st_pat_anon}, PatCross: {st_pat_cross}")

    print("================================================================================")
    print("ALL 14 PHASE 5.1 SECURITY HARDENING CHECKS PASSED (100%)")
    print("================================================================================")

if __name__ == "__main__":
    run_tests()
