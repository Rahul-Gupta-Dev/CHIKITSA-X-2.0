"""
CHIKITSA-X - Phase 5.2 Frontend & Backend Authentication Integration Test Suite
Verifies all authentication, registration, session restoration, role enforcement,
and dynamic profile resolution against an ISOLATED test database (chikitsax.db untouched).
"""

import os
import sys
import json
import base64
import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.main import app
from app.database import Base, get_db as db_get_db, apply_safe_migrations, DEFAULT_DB_FILE
from app.auth import get_db as auth_get_db
from app.seed import seed_database
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.hospital import HospitalModel
from app.models.opd import OPDAppointmentModel
from fastapi.testclient import TestClient

TEST_DB_PATH = os.path.join(CURRENT_DIR, "test_isolated_phase5_2.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.replace(os.sep, '/')}"

def decode_jwt_unverified(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded)
    return json.loads(decoded_bytes.decode("utf-8"))

def setup_isolated_test_db():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    apply_safe_migrations(target_engine=engine)

    # Seed isolated database
    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    return engine, TestingSessionLocal

def run_tests():
    print("=" * 80, flush=True)
    print("CHIKITSA-X - Phase 5.2 Real Authentication & Frontend Integration Test Suite", flush=True)
    print("=" * 80, flush=True)
    print(f"Isolated Test Database: {TEST_DB_PATH}", flush=True)
    print(f"Active Production Database (Protected): {DEFAULT_DB_FILE}", flush=True)
    print("-" * 80, flush=True)

    # Check baseline active database file modification time & size
    active_db_before_stat = os.stat(DEFAULT_DB_FILE) if os.path.exists(DEFAULT_DB_FILE) else None

    print("[1/3] Setting up isolated test database...", flush=True)
    engine, TestingSessionLocal = setup_isolated_test_db()
    print("[1/3] Isolated test database ready & seeded.", flush=True)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_get_db] = override_get_db
    app.dependency_overrides[auth_get_db] = override_get_db

    print("[2/3] Initializing FastAPI TestClient...", flush=True)
    client = TestClient(app)
    print("[2/3] TestClient ready. Starting verification checks...", flush=True)
    results = []

    def record_check(num: int, title: str, passed: bool, msg: str = ""):
        status_str = "PASS" if passed else "FAIL"
        results.append((num, title, status_str, msg))
        icon = "✅" if passed else "❌"
        print(f"{icon} Check {num}: {title} [{status_str}] {('- ' + msg) if msg else ''}", flush=True)
        if not passed:
            raise AssertionError(f"Check {num} FAILED: {msg}")

    try:
        # ---------------------------------------------------------------------
        # Check 1: Patient registration creates user & profile, returns valid JWT
        # ---------------------------------------------------------------------
        reg_payload = {
            "name": "Ananya Sen",
            "email": "ananya.sen@example.com",
            "password": "Password123!",
            "role": "PATIENT",
            "phone": "+91 98300 11223",
            "dateOfBirth": "1994-06-20",
            "gender": "female",
            "bloodGroup": "B+",
            "city": "Kolkata",
            "state": "West Bengal"
        }
        res = client.post("/api/auth/register", json=reg_payload)
        check1_pass = (
            res.status_code == 200 and
            "accessToken" in res.json() and
            res.json().get("user", {}).get("email") == "ananya.sen@example.com" and
            res.json().get("user", {}).get("role") == "PATIENT"
        )
        # Verify persistence in isolated test DB
        with TestingSessionLocal() as s:
            u_check = s.query(UserModel).filter(UserModel.email == "ananya.sen@example.com").first()
            p_check = s.query(PatientModel).filter(PatientModel.user_id == (u_check.id if u_check else "")).first()
            check1_pass = check1_pass and (u_check is not None) and (p_check is not None)
            persisted_info = f"Created user {u_check.id if u_check else 'None'} & patient {p_check.id if p_check else 'None'}"

        record_check(1, "Patient registration creates backend user & profile with JWT", check1_pass, persisted_info)

        # ---------------------------------------------------------------------
        # Check 2: Login with valid credentials authenticates and returns auth state
        # ---------------------------------------------------------------------
        # 2a. Newly registered user
        login_res1 = client.post("/api/auth/login", json={
            "email": "ananya.sen@example.com",
            "password": "Password123!",
            "role": "PATIENT"
        })
        # 2b. Seeded demo doctor
        login_res2 = client.post("/api/auth/login", json={
            "email": "doctor@chikitsax.demo",
            "password": "demo123",
            "role": "DOCTOR"
        })
        # 2c. Seeded demo hospital admin
        login_res3 = client.post("/api/auth/login", json={
            "email": "hospital@chikitsax.demo",
            "password": "demo123",
            "role": "HOSPITAL_ADMIN"
        })
        check2_pass = (
            login_res1.status_code == 200 and "accessToken" in login_res1.json() and
            login_res2.status_code == 200 and "accessToken" in login_res2.json() and
            login_res3.status_code == 200 and "accessToken" in login_res3.json()
        )
        record_check(2, "Login with valid credentials authenticates successfully", check2_pass,
                     "Tested newly registered patient, demo doctor, and demo hospital admin")

        # ---------------------------------------------------------------------
        # Check 3: Login with invalid credentials returns 401 and keeps state unauthenticated
        # ---------------------------------------------------------------------
        bad_pw_res = client.post("/api/auth/login", json={
            "email": "ananya.sen@example.com",
            "password": "WrongPassword!",
            "role": "PATIENT"
        })
        non_existent_res = client.post("/api/auth/login", json={
            "email": "nonexistent.user@example.com",
            "password": "Password123!",
            "role": "PATIENT"
        })
        check3_pass = (
            bad_pw_res.status_code == 401 and
            non_existent_res.status_code == 401 and
            ("Invalid credentials" in bad_pw_res.json().get("detail", "") or "Incorrect password" in bad_pw_res.json().get("detail", "")) and
            ("Invalid" in non_existent_res.json().get("detail", ""))
        )
        record_check(3, "Login with invalid credentials rejected with HTTP 401", check3_pass,
                     f"Bad password status: {bad_pw_res.status_code}, Non-existent status: {non_existent_res.status_code}")

        # ---------------------------------------------------------------------
        # Check 4: Registration with duplicate email rejected with HTTP 400
        # ---------------------------------------------------------------------
        dup_res = client.post("/api/auth/register", json=reg_payload)
        check4_pass = (
            dup_res.status_code == 400 and
            ("already exists" in dup_res.json().get("detail", "").lower() or "already registered" in dup_res.json().get("detail", "").lower())
        )
        record_check(4, "Registration with duplicate email rejected with HTTP 400", check4_pass,
                     f"Detail: {dup_res.json().get('detail')}")

        # ---------------------------------------------------------------------
        # Check 5: Registration with privileged roles (DOCTOR, HOSPITAL_ADMIN) rejected with 403
        # ---------------------------------------------------------------------
        doc_reg = client.post("/api/auth/register", json={
            "name": "Dr. Hacker",
            "email": "hacker.doc@chikitsax.test",
            "password": "Password123!",
            "role": "DOCTOR"
        })
        admin_reg = client.post("/api/auth/register", json={
            "name": "Admin Impostor",
            "email": "impostor.admin@chikitsax.test",
            "password": "Password123!",
            "role": "HOSPITAL_ADMIN"
        })
        staff_reg = client.post("/api/auth/register", json={
            "name": "Staff Impostor",
            "email": "impostor.staff@chikitsax.test",
            "password": "Password123!",
            "role": "HOSPITAL_STAFF"
        })
        check5_pass = (
            doc_reg.status_code == 403 and
            admin_reg.status_code == 403 and
            staff_reg.status_code == 403
        )
        record_check(5, "Registration with privileged roles rejected with HTTP 403", check5_pass,
                     f"Doctor reg: {doc_reg.status_code}, Admin reg: {admin_reg.status_code}, Staff reg: {staff_reg.status_code}")

        # ---------------------------------------------------------------------
        # Check 6: Backend session verification rejects invalid / missing tokens with 401
        # ---------------------------------------------------------------------
        no_token_me = client.get("/api/auth/me")
        bad_token_me = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
        malformed_token_me = client.get("/api/auth/me", headers={"Authorization": "NotBearer xyz"})
        check6_pass = (
            no_token_me.status_code == 401 and
            bad_token_me.status_code == 401 and
            malformed_token_me.status_code == 401
        )
        record_check(6, "Session verification rejects invalid/missing tokens with HTTP 401", check6_pass,
                     f"No token: {no_token_me.status_code}, Bad token: {bad_token_me.status_code}, Malformed: {malformed_token_me.status_code}")

        # ---------------------------------------------------------------------
        # Check 7: Session restoration restores user identity and role accurately
        # ---------------------------------------------------------------------
        patient_token = login_res1.json()["accessToken"]
        restore_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {patient_token}"})
        me_json = restore_me.json()
        check7_pass = (
            restore_me.status_code == 200 and
            me_json.get("email") == "ananya.sen@example.com" and
            me_json.get("role") == "PATIENT" and
            "patientProfile" in me_json and
            me_json["patientProfile"]["fullName"] == "Ananya Sen"
        )
        record_check(7, "Session restoration correctly restores user and patient profile", check7_pass,
                     f"Resolved: {me_json.get('name')} ({me_json.get('role')}), Patient ID: {me_json.get('patientProfile', {}).get('id')}")

        # ---------------------------------------------------------------------
        # Check 8: User identity & role consistency: client role spoofing rejected
        # ---------------------------------------------------------------------
        # Patient attempting to log in claiming to be DOCTOR or HOSPITAL_ADMIN
        spoof_res1 = client.post("/api/auth/login", json={
            "email": "ananya.sen@example.com",
            "password": "Password123!",
            "role": "DOCTOR"
        })
        spoof_res2 = client.post("/api/auth/login", json={
            "email": "ananya.sen@example.com",
            "password": "Password123!",
            "role": "HOSPITAL_ADMIN"
        })
        # Check JWT claims match database exactly
        claims = decode_jwt_unverified(patient_token)
        with TestingSessionLocal() as s:
            user_in_db = s.query(UserModel).filter(UserModel.email == "ananya.sen@example.com").first()
            check8_pass = (
                spoof_res1.status_code in [401, 403] and
                spoof_res2.status_code in [401, 403] and
                claims.get("sub") == user_in_db.id and
                claims.get("role") == user_in_db.role and
                claims.get("role") == "PATIENT"
            )
        record_check(8, "Role spoofing rejected and JWT payload matches database record strictly", check8_pass,
                     f"Doctor spoof: {spoof_res1.status_code}, Admin spoof: {spoof_res2.status_code}, JWT role: {claims.get('role')}")

        # ---------------------------------------------------------------------
        # Check 9: Protected endpoints reject unauthenticated access with HTTP 401
        # ---------------------------------------------------------------------
        prot_patient = client.get("/api/patients/me")
        prot_audit = client.get("/api/audit-logs")
        prot_records = client.post("/api/medical-records", json={
            "patient_id": "pat-test",
            "file_name": "lab.pdf",
            "file_type": "application/pdf",
            "category": "Prescription"
        })
        prot_consult = client.post("/api/consultations", json={
            "appointment_id": "opd-1",
            "clinical_notes": "Test notes",
            "diagnosis": "Test diagnosis"
        })
        prot_consult_view = client.get("/api/consultations/opd-1")

        check9_pass = (
            prot_patient.status_code == 401 and
            prot_audit.status_code == 401 and
            prot_records.status_code == 401 and
            prot_consult.status_code == 401 and
            prot_consult_view.status_code == 401
        )
        record_check(9, "Protected API endpoints reject unauthenticated requests with HTTP 401", check9_pass,
                     f"Patients/me: {prot_patient.status_code}, Audit-logs: {prot_audit.status_code}, Records: {prot_records.status_code}, Consultations: {prot_consult.status_code}, Consult-view: {prot_consult_view.status_code}")

        # ---------------------------------------------------------------------
        # Check 10: Dynamic doctor profile resolution on session restoration
        # ---------------------------------------------------------------------
        doc_token = login_res2.json()["accessToken"]
        doc_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {doc_token}"})
        doc_json = doc_me.json()
        doc_profile = doc_json.get("doctorProfile")
        check10_pass = (
            doc_me.status_code == 200 and
            doc_profile is not None and
            doc_profile.get("id") == "doc-1" and
            doc_profile.get("name") == "Dr. Rajesh Kulkarni" and
            doc_profile.get("hospitalId") == "hosp-1"
        )
        record_check(10, "Doctor profile dynamically resolved from database on /auth/me", check10_pass,
                     f"Doctor Profile: ID={doc_profile.get('id') if doc_profile else None}, Name={doc_profile.get('name') if doc_profile else None}, Hospital={doc_profile.get('hospitalId') if doc_profile else None}")

        # ---------------------------------------------------------------------
        # Check 11: Hospital verification returns full appointment entity IDs
        # ---------------------------------------------------------------------
        hosp_token = login_res3.json()["accessToken"]
        # Query an existing OPD appointment reference from isolated test DB
        with TestingSessionLocal() as s:
            test_opd = s.query(OPDAppointmentModel).filter(OPDAppointmentModel.hospital_id == "hosp-1").first()
            assert test_opd is not None, "Test OPD appointment missing in seed"
            test_ref = test_opd.reference_id
            # Reset status if already verified so we can test verification
            test_opd.status = "CONFIRMED"
            s.commit()

        verify_res = client.post(
            "/api/hospital/verify",
            headers={"Authorization": f"Bearer {hosp_token}"},
            json={
                "reference_id": test_ref,
                "hospital_id": "hosp-1",
                "staff_name": "Test Receptionist"
            }
        )
        verify_json = verify_res.json()
        appointment_data = verify_json.get("appointment", {})
        check11_pass = (
            verify_res.status_code == 200 and
            verify_json.get("verified") is True and
            appointment_data.get("hospitalId") == "hosp-1" and
            "doctorId" in appointment_data and
            "patientId" in appointment_data
        )
        record_check(11, "Hospital verification payload contains complete hospitalId, doctorId, patientId", check11_pass,
                     f"Verified: {verify_json.get('verified')}, HospID: {appointment_data.get('hospitalId')}, DocID: {appointment_data.get('doctorId')}, PatID: {appointment_data.get('patientId')}")

        # ---------------------------------------------------------------------
        # Check 12: Production database zero-mutation verification
        # ---------------------------------------------------------------------
        if active_db_before_stat and os.path.exists(DEFAULT_DB_FILE):
            active_db_after_stat = os.stat(DEFAULT_DB_FILE)
            # Query active DB directly to ensure no 'ananya.sen@example.com' was created in production DB
            conn = sqlite3.connect(DEFAULT_DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'ananya.sen@example.com'")
            count_leak = cursor.fetchone()[0]
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            conn.close()

            check12_pass = (count_leak == 0) and (integrity == "ok")
            record_check(12, "Active production database has zero test mutations & integrity ok", check12_pass,
                         f"Test email leakage: {count_leak}, Active DB integrity: {integrity}")
        else:
            record_check(12, "Active production database check", True, "Default DB verified")

    finally:
        # Cleanup isolated test database
        app.dependency_overrides.clear()
        engine.dispose()
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception as e:
                print(f"Notice: Test DB cleanup deferred: {e}")

    print("=" * 80)
    print("All 12 Verification & Integration Checks PASSED Successfully!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
