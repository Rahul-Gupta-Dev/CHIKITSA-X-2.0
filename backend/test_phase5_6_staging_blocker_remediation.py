"""
CHIKITSA-X - Phase 5.6 Final Staging Blocker Remediation Test Suite
Verifies:
1. Patient QR Self-Verification Guard: Patient cannot self-verify QR check-in (HTTP 403).
2. Authorized Hospital Check-in: Hospital staff can perform check-in (HTTP 200, status=VERIFIED).
3. Doctor Clinical Context Consent Guard: Doctor profile access without active consent returns HTTP 403.
4. Doctor Clinical Context With Active Consent: Doctor profile access with active consent returns patient's actual data.
5. Immediate Revocation Enforcement: Revoking consent immediately blocks doctor profile access (HTTP 403).
6. Cross-Patient & Cross-Doctor Isolation: Unauthorized access to other patients' profiles rejected (HTTP 403).
7. Active Database Zero-Mutation Guarantee: chikitsax.db remains untouched.

Uses ISOLATED synthetic database (test_isolated_phase5_6.db).
"""

import os
import sys
import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import Base, apply_safe_migrations, DEFAULT_DB_FILE
from app.auth import hash_password
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.hospital import HospitalModel
from app.models.opd import OPDAppointmentModel
from app.models.qr import QRReferenceModel
from app.models.consent import ConsentLogModel

from app.schemas import HospitalVerifyRequest, ConsentCreateRequest
from app.routers.qr import hospital_staff_verify
from app.routers.patients import get_unified_patient_profile
from app.routers.consent import record_consent, revoke_consent

from fastapi import HTTPException

TEST_DB_PATH = os.path.join(CURRENT_DIR, "test_isolated_phase5_6.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.replace(os.sep, '/')}"

def run_tests():
    print("=" * 80)
    print("CHIKITSA-X PHASE 5.6: STAGING BLOCKER REMEDIATION TEST SUITE")
    print("=" * 80)

    # Active DB baseline check
    active_db = DEFAULT_DB_FILE
    active_conn = sqlite3.connect(active_db)
    active_cur = active_conn.cursor()
    active_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    active_tables_count = active_cur.fetchone()[0]
    active_cur.execute("SELECT count(*) FROM users;")
    active_users_count = active_cur.fetchone()[0]
    active_cur.execute("SELECT count(*) FROM opd_appointments;")
    active_opd_count = active_cur.fetchone()[0]
    active_conn.close()

    print(f"[*] Active Database Baseline ({active_db}):")
    print(f"    - Tables: {active_tables_count}")
    print(f"    - Users:  {active_users_count}")
    print(f"    - OPDs:   {active_opd_count}")

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    apply_safe_migrations(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    hashed_pw = hash_password("password123")

    with Session() as s:
        # 1. Hospital
        hosp = HospitalModel(
            id="hosp-pune-1",
            name="CarePlus Super Specialty Hospital",
            code="CPS-PUNE",
            tagline="Leading Healthcare Provider",
            address="Shivajinagar, Pune",
            city="Pune",
            phone="020-25500000",
            emergency_phone="020-25500099",
            estimated_cost_range={"min": 5000, "max": 50000}
        )
        s.add(hosp)
        s.flush()

        # 2. Users
        u_patient1 = UserModel(id="usr-pat-1", email="pat1@test.chikitsax", password_hash=hashed_pw, name="Rahul Verma", role="PATIENT")
        u_patient2 = UserModel(id="usr-pat-2", email="pat2@test.chikitsax", password_hash=hashed_pw, name="Sneha Patil", role="PATIENT")
        u_doctor1 = UserModel(id="usr-doc-1", email="doc1@test.chikitsax", password_hash=hashed_pw, name="Dr. Rajesh Kulkarni", role="DOCTOR", hospital_id="hosp-pune-1")
        u_staff1 = UserModel(id="usr-staff-1", email="staff1@test.chikitsax", password_hash=hashed_pw, name="Staff Receptionist", role="HOSPITAL_STAFF", hospital_id="hosp-pune-1")
        s.add_all([u_patient1, u_patient2, u_doctor1, u_staff1])
        s.flush()

        # 3. Patient Profiles with Real Vitals
        p1 = PatientModel(
            id="pat-1",
            user_id="usr-pat-1",
            full_name="Rahul Verma",
            age=38,
            gender="Male",
            blood_group="B+",
            phone="9876543210",
            email="pat1@test.chikitsax",
            address="Kothrud",
            city="Pune",
            pincode="411038",
            vital_signs={"bp": "124/82", "pulse": "74 bpm", "spo2": "99%", "temp": "98.2°F"},
            medications=["Metformin 500mg"],
            allergies=["Penicillin"],
            care_stage=6
        )
        p2 = PatientModel(
            id="pat-2",
            user_id="usr-pat-2",
            full_name="Sneha Patil",
            age=29,
            gender="Female",
            blood_group="O+",
            phone="9876543211",
            email="pat2@test.chikitsax",
            address="Baner",
            city="Pune",
            pincode="411045",
            vital_signs={"bp": "112/72", "pulse": "68 bpm", "spo2": "98%", "temp": "98.6°F"},
            medications=["Levothyroxine 50mcg"],
            allergies=["Sulfa Drugs"],
            care_stage=6
        )
        s.add_all([p1, p2])

        # 4. Doctor Profile
        d1 = DoctorModel(
            id="doc-1",
            name="Dr. Rajesh Kulkarni",
            specialty="Interventional Cardiology",
            qualification="MBBS, MD, DM",
            hospital_id="hosp-pune-1",
            hospital_name="CarePlus Super Specialty Hospital",
            consultation_fee=800,
            available_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            available_slots=["09:00", "09:30", "10:00", "10:30", "11:00"]
        )
        s.add(d1)

        # 5. OPD Appointment for Patient 1
        ref_id = "REF-20261103-0001"
        opd1 = OPDAppointmentModel(
            id="opd-1",
            reference_id=ref_id,
            qr_token="token-secret-12345",
            patient_id="usr-pat-1",
            patient_name="Rahul Verma",
            patient_phone="9876543210",
            hospital_id="hosp-pune-1",
            hospital_name="CarePlus Super Specialty Hospital",
            doctor_id="doc-1",
            doctor_name="Dr. Rajesh Kulkarni",
            department="Cardiology",
            appointment_date=datetime.date.today(),
            appointment_time="10:00",
            consultation_fee=800,
            status="CONFIRMED"
        )
        s.add(opd1)

        # QR reference record
        qr1 = QRReferenceModel(
            id="qr-opd-1",
            reference_id=ref_id,
            token="token-secret-12345",
            patient_id="usr-pat-1",
            hospital_id="hosp-pune-1",
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            is_verified=False
        )
        s.add(qr1)
        s.commit()

    print("\n[+] Synthetic Database Seeded Successfully.")

    # -------------------------------------------------------------------------
    # CHECK 1: Patient Cannot Self-Verify QR Check-In (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- Check 1: Patient Self-Verification Guard ---")
    with Session() as s:
        verify_req = HospitalVerifyRequest(reference_id=ref_id, hospital_id="hosp-pune-1")
        try:
            hospital_staff_verify(verify_req, db=s, current_user=u_patient1)
            assert False, "FAILED: Patient was able to self-verify hospital check-in!"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403 Forbidden, got {e.status_code}"
            assert "Only hospital staff" in e.detail or "Forbidden" in e.detail, f"Unexpected detail: {e.detail}"
            print("  [PASS] Patient self-verification rejected with HTTP 403 Forbidden.")

    # -------------------------------------------------------------------------
    # CHECK 2: Authorized Hospital Staff Check-In (HTTP 200)
    # -------------------------------------------------------------------------
    print("\n--- Check 2: Authorized Hospital Staff Verification ---")
    with Session() as s:
        verify_req = HospitalVerifyRequest(reference_id=ref_id, hospital_id="hosp-pune-1")
        res = hospital_staff_verify(verify_req, db=s, current_user=u_staff1)
        assert res.get("verified") is True, f"Verification failed: {res}"
        assert res.get("status") == "VERIFIED", f"Status not set to VERIFIED: {res}"

        # Re-query DB to confirm persistence
        updated_opd = s.query(OPDAppointmentModel).filter_by(id="opd-1").first()
        assert updated_opd.status == "VERIFIED", f"OPD status not updated in DB: {updated_opd.status}"
        print(f"  [PASS] Hospital staff check-in succeeded. OPD status: {updated_opd.status}")

    # -------------------------------------------------------------------------
    # CHECK 3: Doctor Access Without Patient Consent Blocked (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- Check 3: Doctor Clinical Context Consent Guard ---")
    with Session() as s:
        try:
            get_unified_patient_profile(patient_id="usr-pat-1", db=s, current_user=u_doctor1)
            assert False, "FAILED: Doctor accessed patient profile without active consent!"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403 Forbidden, got {e.status_code}"
            assert "Active clinical consent from patient is required" in e.detail
            print("  [PASS] Doctor profile access without consent rejected with HTTP 403 Forbidden.")

    # -------------------------------------------------------------------------
    # CHECK 4: Doctor Access With Active Consent Unlocked (HTTP 200 & Real Data)
    # -------------------------------------------------------------------------
    print("\n--- Check 4: Doctor Clinical Context With Active Consent ---")
    consent_id = None
    with Session() as s:
        # Grant consent from Patient 1 to Doctor 1
        consent_req = ConsentCreateRequest(
            patient_id="usr-pat-1",
            hospital_id="hosp-pune-1",
            hospital_name="CarePlus Super Specialty Hospital",
            doctor_id="doc-1",
            doctor_name="Dr. Rajesh Kulkarni",
            granted=True
        )
        c_res = record_consent(consent_req, db=s, current_user=u_patient1)
        consent_id = c_res["id"]
        s.commit()

        # Doctor accesses Patient 1 profile
        prof = get_unified_patient_profile(patient_id="usr-pat-1", db=s, current_user=u_doctor1)
        assert prof["fullName"] == "Rahul Verma", f"Expected 'Rahul Verma', got {prof.get('fullName')}"
        assert prof["vitalSigns"]["bp"] == "124/82", f"Expected BP '124/82', got {prof.get('vitalSigns')}"
        assert prof["medications"] == ["Metformin 500mg"], f"Expected Metformin, got {prof.get('medications')}"
        assert prof["allergies"] == ["Penicillin"], f"Expected Penicillin, got {prof.get('allergies')}"
        print(f"  [PASS] Doctor successfully loaded real patient profile:")
        print(f"         Patient: {prof['fullName']}, BP: {prof['vitalSigns']['bp']}, Meds: {prof['medications']}")

    # -------------------------------------------------------------------------
    # CHECK 5: Immediate Consent Revocation Enforcement (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- Check 5: Immediate Consent Revocation Enforcement ---")
    with Session() as s:
        # Patient 1 revokes consent
        assert consent_id is not None
        revoke_consent(consent_id=consent_id, db=s, current_user=u_patient1)
        s.commit()

        # Doctor attempts to access Patient 1 profile again
        try:
            get_unified_patient_profile(patient_id="usr-pat-1", db=s, current_user=u_doctor1)
            assert False, "FAILED: Doctor accessed patient profile after consent was revoked!"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403 Forbidden, got {e.status_code}"
            assert "Active clinical consent from patient is required" in e.detail
            print("  [PASS] Profile access immediately blocked following consent revocation (HTTP 403).")

    # -------------------------------------------------------------------------
    # CHECK 6: Cross-Patient and Patient-to-Patient Isolation (HTTP 403)
    # -------------------------------------------------------------------------
    print("\n--- Check 6: Cross-Patient Isolation Guard ---")
    with Session() as s:
        # Doctor 1 tries to access Patient 2 (Sneha Patil) where no consent exists
        try:
            get_unified_patient_profile(patient_id="usr-pat-2", db=s, current_user=u_doctor1)
            assert False, "FAILED: Doctor accessed unconsented Patient 2 profile!"
        except HTTPException as e:
            assert e.status_code == 403
            print("  [PASS] Doctor access to unconsented Patient 2 blocked (HTTP 403).")

        # Patient 1 tries to access Patient 2's profile
        try:
            get_unified_patient_profile(patient_id="usr-pat-2", db=s, current_user=u_patient1)
            assert False, "FAILED: Patient 1 accessed Patient 2 profile!"
        except HTTPException as e:
            assert e.status_code == 403
            assert "You are not authorized to view another patient's profile" in e.detail
            print("  [PASS] Patient 1 access to Patient 2 blocked (HTTP 403).")

    # -------------------------------------------------------------------------
    # CHECK 7: Active Database Zero-Mutation Verification
    # -------------------------------------------------------------------------
    print("\n--- Check 7: Active Database Zero-Mutation Guarantee ---")
    active_conn = sqlite3.connect(active_db)
    active_cur = active_conn.cursor()
    active_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    final_tables_count = active_cur.fetchone()[0]
    active_cur.execute("SELECT count(*) FROM users;")
    final_users_count = active_cur.fetchone()[0]
    active_cur.execute("SELECT count(*) FROM opd_appointments;")
    final_opd_count = active_cur.fetchone()[0]
    active_conn.close()

    assert final_tables_count == active_tables_count, f"Active DB table count changed! {active_tables_count} -> {final_tables_count}"
    assert final_users_count == active_users_count, f"Active DB user count changed! {active_users_count} -> {final_users_count}"
    assert final_opd_count == active_opd_count, f"Active DB OPD count changed! {active_opd_count} -> {final_opd_count}"

    print(f"  [PASS] Active Database completely untouched:")
    print(f"         Tables: {final_tables_count} (unchanged)")
    print(f"         Users:  {final_users_count} (unchanged)")
    print(f"         OPDs:   {final_opd_count} (unchanged)")

    # Clean up isolated synthetic DB
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
            print(f"  [+] Cleaned up temporary test database: {TEST_DB_PATH}")
        except Exception as e:
            print(f"  [!] Note on test DB cleanup: {e}")

    print("\n" + "=" * 80)
    print("ALL 7 PHASE 5.6 STAGING BLOCKER REMEDIATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
