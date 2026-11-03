"""
CHIKITSA-X - Phase 5.5 Multi-User End-to-End Production Readiness Test Suite
Verifies:
1. Patient Isolation (Patient A cannot read Patient B's records / files).
2. Doctor Appointment Isolation (Doctor B cannot access Doctor A's queue).
3. Hospital Staff Scoping (Staff cannot access another hospital's OPD queue).
4. Clinical Consent Lifecycle (Doctor access blocked without consent, granted, and immediately blocked upon revocation).
5. Cross-Hospital QR Check-In Scoping (Staff B cannot verify Hospital A passes).
6. Doctor Consultation Draft Isolation (Unauthorized doctors & patients blocked from reading drafts).
7. Duplicate Consultation Prevention (Finalization cannot be duplicated, returns 409).
8. Concurrent Slot Double-Booking Prevention (Multithreaded booking collision returns 409).
9. Active Database Zero-Mutation Guarantee (chikitsax.db untouched).

Uses ISOLATED synthetic database (test_isolated_phase5_5.db).
"""

import os
import sys
import threading
import sqlite3
import datetime
from sqlalchemy import create_engine, text
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
from app.models.medical_record import MedicalRecordModel
from app.models.consent import ConsentLogModel
from app.models.consultation import ConsultationModel, ConsultationDraftModel

from app.schemas import (
    OPDCreateRequest,
    ConsultationCreateRequest,
    ConsultationDraftRequest,
    HospitalVerifyRequest,
    ConsentCreateRequest
)

from app.routers.medical_records import get_records_by_patient, download_record_file
from app.routers.doctors import get_doctor_appointments
from app.routers.opd import list_opd_appointments, create_opd_appointment
from app.routers.consent import record_consent, revoke_consent
from app.routers.qr import hospital_staff_verify
from app.routers.consultations import save_consultation_draft, get_consultation_draft, record_consultation

from fastapi import HTTPException

TEST_DB_PATH = os.path.join(CURRENT_DIR, "test_isolated_phase5_5.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.replace(os.sep, '/')}"

def run_tests():
    print("=" * 80)
    print("CHIKITSA-X PHASE 5.5: MULTI-USER END-TO-END PRODUCTION READINESS TESTS")
    print("=" * 80)

    # Active DB baseline
    active_db = DEFAULT_DB_FILE
    active_conn = sqlite3.connect(active_db)
    active_cur = active_conn.cursor()
    active_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    active_tables_count = active_cur.fetchone()[0]
    active_cur.execute("SELECT count(*) FROM users;")
    active_users_count = active_cur.fetchone()[0]
    active_conn.close()

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    apply_safe_migrations(engine)
    Session = sessionmaker(bind=engine)

    # Setup 6 Synthetic Test Accounts
    # Patient A, Patient B, Doctor A (Hosp A), Doctor B (Hosp B), Staff A (Hosp A), Staff B (Hosp B)
    hashed_pw = hash_password("password123")

    with Session() as s:
        # Hospitals
        hosp_a = HospitalModel(id="hosp-A", name="Apollo Apex Hospital", code="APH-PUNE", tagline="Apex Tertiary Care",
                               address="FC Road", city="Pune", phone="020-111111", emergency_phone="020-111119",
                               estimated_cost_range={"min": 10000, "max": 50000})
        hosp_b = HospitalModel(id="hosp-B", name="Ruby Metro Hospital", code="RMH-PUNE", tagline="Metro Healthcare",
                               address="Camp", city="Pune", phone="020-222222", emergency_phone="020-222229",
                               estimated_cost_range={"min": 8000, "max": 40000})
        s.add_all([hosp_a, hosp_b])
        s.flush()

        # Users
        u_pat_a = UserModel(id="usr-pat-A", email="pata@test.chikitsax", password_hash=hashed_pw, name="Patient A", role="PATIENT")
        u_pat_b = UserModel(id="usr-pat-B", email="patb@test.chikitsax", password_hash=hashed_pw, name="Patient B", role="PATIENT")
        u_doc_a = UserModel(id="usr-doc-A", email="doca@test.chikitsax", password_hash=hashed_pw, name="Dr. Alice Vance", role="DOCTOR", hospital_id="hosp-A")
        u_doc_b = UserModel(id="usr-doc-B", email="docb@test.chikitsax", password_hash=hashed_pw, name="Dr. Bob Vance", role="DOCTOR", hospital_id="hosp-B")
        u_stf_a = UserModel(id="usr-stf-A", email="staffa@test.chikitsax", password_hash=hashed_pw, name="Staff Alice", role="HOSPITAL_STAFF", hospital_id="hosp-A")
        u_stf_b = UserModel(id="usr-stf-B", email="staffb@test.chikitsax", password_hash=hashed_pw, name="Staff Bob", role="HOSPITAL_STAFF", hospital_id="hosp-B")
        s.add_all([u_pat_a, u_pat_b, u_doc_a, u_doc_b, u_stf_a, u_stf_b])
        s.flush()

        # Patient Profiles
        p_pat_a = PatientModel(id="pat-A", user_id="usr-pat-A", full_name="Patient A", age=35, gender="Female",
                               blood_group="A+", phone="+91 91111 11111", email="pata@test.chikitsax", address="Street A",
                               city="Pune", pincode="411001", care_stage=1)
        p_pat_b = PatientModel(id="pat-B", user_id="usr-pat-B", full_name="Patient B", age=42, gender="Male",
                               blood_group="B+", phone="+91 92222 22222", email="patb@test.chikitsax", address="Street B",
                               city="Pune", pincode="411002", care_stage=1)
        s.add_all([p_pat_a, p_pat_b])
        s.flush()

        # Doctor Profiles
        doc_a = DoctorModel(id="doc-A", hospital_id="hosp-A", hospital_name="Apollo Apex Hospital",
                            name="Dr. Alice Vance", specialty="Cardiology", qualification="MBBS, MD", consultation_fee=700)
        doc_b = DoctorModel(id="doc-B", hospital_id="hosp-B", hospital_name="Ruby Metro Hospital",
                            name="Dr. Bob Vance", specialty="Neurology", qualification="MBBS, MD", consultation_fee=800)
        s.add_all([doc_a, doc_b])
        s.flush()

        # Patient A Uploads Medical Record (Synthetic file)
        upload_test_dir = os.path.join(CURRENT_DIR, "uploads", "medical_records")
        os.makedirs(upload_test_dir, exist_ok=True)
        test_file_path = os.path.join(upload_test_dir, "test_synth_record_A.txt")
        with open(test_file_path, "w", encoding="utf-8") as tf:
            tf.write("SYNTHETIC CLINICAL ECG REPORT - PATIENT A ONLY")

        rec_a = MedicalRecordModel(
            id="rec-A-1",
            patient_id="pat-A",
            category="Lab Report",
            file_name="test_synth_record_A.txt",
            file_type="text/plain",
            file_path=os.path.abspath(test_file_path),
            upload_date="2026-11-03",
            ocr_extracted_data={"text": "SYNTHETIC CLINICAL ECG REPORT"},
            is_verified_by_patient=True
        )
        s.add(rec_a)
        s.commit()

    results = []
    def record_check(num: int, title: str, passed: bool, msg: str = ""):
        status_str = "PASS" if passed else "FAIL"
        results.append((num, title, status_str, msg))
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"{icon} Check {num}: {title} {('- ' + msg) if msg else ''}", flush=True)

    # --------------------------------------------------------------------------
    # Check 1: Patient A cannot read Patient B's records (IDOR Protection)
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_b = s.query(UserModel).filter(UserModel.id == "usr-pat-B").first()
            idor_records_blocked = False
            try:
                get_records_by_patient(patient_id="pat-A", db=s, current_user=u_b)
            except HTTPException as he:
                if he.status_code == 403:
                    idor_records_blocked = True

            idor_download_blocked = False
            try:
                download_record_file(record_id="rec-A-1", db=s, current_user=u_b)
            except HTTPException as he:
                if he.status_code == 403:
                    idor_download_blocked = True

        passed = idor_records_blocked and idor_download_blocked
        record_check(1, "Cross-Patient Record Isolation (IDOR Protection)", passed,
                     f"Record list blocked={idor_records_blocked}, File download blocked={idor_download_blocked}")
    except Exception as e:
        record_check(1, "Cross-Patient Record Isolation (IDOR Protection)", False, str(e))

    # --------------------------------------------------------------------------
    # Check 2: Doctor Appointment Isolation
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_da = s.query(UserModel).filter(UserModel.id == "usr-doc-A").first()
            u_db = s.query(UserModel).filter(UserModel.id == "usr-doc-B").first()
            p_a = s.query(UserModel).filter(UserModel.id == "usr-pat-A").first()

            # Patient A books appointment with Doctor A
            opd_a = create_opd_appointment(
                payload=OPDCreateRequest(
                    patient_id="pat-A",
                    hospital_id="hosp-A",
                    doctor_id="doc-A",
                    department="Cardiology",
                    appointment_date="2026-11-20",
                    appointment_time="10:00 AM"
                ),
                db=s,
                current_user=p_a
            )

            # Doctor B attempts to view Doctor A's queue
            doc_b_blocked = False
            try:
                get_doctor_appointments(doctor_id="doc-A", db=s, current_user=u_db)
            except HTTPException as he:
                if he.status_code == 403:
                    doc_b_blocked = True

            # Doctor A views own queue
            doc_a_view = get_doctor_appointments(doctor_id="doc-A", db=s, current_user=u_da)
            doc_a_allowed = len(doc_a_view) >= 1

        passed = doc_b_blocked and doc_a_allowed
        record_check(2, "Doctor Appointment Isolation", passed,
                     f"Doctor B blocked from Doc A queue={doc_b_blocked}, Doctor A accessed own queue={doc_a_allowed}")
    except Exception as e:
        record_check(2, "Doctor Appointment Isolation", False, str(e))

    # --------------------------------------------------------------------------
    # Check 3: Cross-Hospital Staff Scoping
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_sa = s.query(UserModel).filter(UserModel.id == "usr-stf-A").first()
            u_sb = s.query(UserModel).filter(UserModel.id == "usr-stf-B").first()

            # Staff B (at hosp-B) queries appointments specifying hosp-A -> must be blocked with 403
            sb_blocked_from_hosp_a = False
            try:
                list_opd_appointments(hospital_id="hosp-A", db=s, current_user=u_sb)
            except HTTPException as he:
                if he.status_code == 403:
                    sb_blocked_from_hosp_a = True

            # Staff B querying own hospital (hosp-B) succeeds
            sb_own_view = list_opd_appointments(hospital_id="hosp-B", db=s, current_user=u_sb)
            sb_saw_hosp_a_data = any(app.get("hospital_id") == "hosp-A" for app in sb_own_view)

            # Staff A (at hosp-A) queries appointments for hosp-A
            sa_view = list_opd_appointments(hospital_id="hosp-A", db=s, current_user=u_sa)
            sa_saw_hosp_a_data = any(app.get("hospital_id") == "hosp-A" for app in sa_view)

        passed = sb_blocked_from_hosp_a and (not sb_saw_hosp_a_data) and sa_saw_hosp_a_data
        record_check(3, "Cross-Hospital Staff Scoping", passed,
                     f"Staff B blocked from Hosp A (403)={sb_blocked_from_hosp_a}, Staff A accessed Hosp A={sa_saw_hosp_a_data}")
    except Exception as e:
        record_check(3, "Cross-Hospital Staff Scoping", False, str(e))

    # --------------------------------------------------------------------------
    # Check 4: Patient Consent Enforced on Doctor Medical-Record Access
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_da = s.query(UserModel).filter(UserModel.id == "usr-doc-A").first()
            u_pa = s.query(UserModel).filter(UserModel.id == "usr-pat-A").first()

            # 4a. Doctor A attempts to read Patient A's records WITHOUT consent -> 403
            doc_a_unconsented_blocked = False
            try:
                get_records_by_patient(patient_id="pat-A", db=s, current_user=u_da)
            except HTTPException as he:
                if he.status_code == 403:
                    doc_a_unconsented_blocked = True

            # 4b. Patient A GRANTS consent to Doctor A
            c_res = record_consent(
                payload=ConsentCreateRequest(
                    patient_id="pat-A",
                    hospital_id="hosp-A",
                    doctor_id="doc-A",
                    doctor_name="Dr. Alice Vance",
                    department="Cardiology",
                    access_scope="ALL"
                ),
                db=s,
                current_user=u_pa
            )
            consent_id = c_res.get("id")

            # 4c. Doctor A attempts to read Patient A's records WITH active consent -> 200
            recs_with_consent = get_records_by_patient(patient_id="pat-A", db=s, current_user=u_da)
            doc_a_consented_allowed = len(recs_with_consent) >= 1

            # 4d. Patient A REVOKES consent
            revoke_consent(consent_id=consent_id, db=s, current_user=u_pa)

            # 4e. Doctor A attempts to read records AFTER revocation -> 403
            doc_a_revoked_blocked = False
            try:
                get_records_by_patient(patient_id="pat-A", db=s, current_user=u_da)
            except HTTPException as he:
                if he.status_code == 403:
                    doc_a_revoked_blocked = True

        passed = doc_a_unconsented_blocked and doc_a_consented_allowed and doc_a_revoked_blocked
        record_check(4, "Patient Consent Lifecycle Enforced on Medical Records", passed,
                     f"Unconsented blocked={doc_a_unconsented_blocked}, Granted allowed={doc_a_consented_allowed}, Revoked blocked={doc_a_revoked_blocked}")
    except Exception as e:
        record_check(4, "Patient Consent Lifecycle Enforced on Medical Records", False, str(e))

    # --------------------------------------------------------------------------
    # Check 5: Cross-Hospital QR Check-In Scoping
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_sb = s.query(UserModel).filter(UserModel.id == "usr-stf-B").first()
            u_sa = s.query(UserModel).filter(UserModel.id == "usr-stf-A").first()
            ref_a = opd_a["reference_id"]

            # 5a. Staff B (hosp-B) attempts to verify appointment at hosp-A -> 403
            staff_b_blocked = False
            try:
                hospital_staff_verify(
                    payload=HospitalVerifyRequest(reference_id=ref_a, hospital_id="hosp-B"),
                    db=s,
                    current_user=u_sb
                )
            except HTTPException as he:
                if he.status_code == 403:
                    staff_b_blocked = True

            # 5b. Staff A (hosp-A) verifies appointment -> 200 OK
            v_res = hospital_staff_verify(
                payload=HospitalVerifyRequest(reference_id=ref_a, hospital_id="hosp-A"),
                db=s,
                current_user=u_sa
            )
            staff_a_allowed = (v_res.get("verified") is True) and (v_res.get("status") == "VERIFIED")

        passed = staff_b_blocked and staff_a_allowed
        record_check(5, "Cross-Hospital QR Check-In Scoping", passed,
                     f"Cross-hospital verify rejected={staff_b_blocked}, Correct hospital verify allowed={staff_a_allowed}")
    except Exception as e:
        record_check(5, "Cross-Hospital QR Check-In Scoping", False, str(e))

    # --------------------------------------------------------------------------
    # Check 6: Doctor Consultation Draft Access Protection
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_da = s.query(UserModel).filter(UserModel.id == "usr-doc-A").first()
            u_db = s.query(UserModel).filter(UserModel.id == "usr-doc-B").first()
            u_pa = s.query(UserModel).filter(UserModel.id == "usr-pat-A").first()
            app_id = opd_a["id"]

            # Doctor A saves draft
            save_consultation_draft(
                payload=ConsultationDraftRequest(
                    appointment_id=app_id,
                    clinical_notes="Confidential preliminary diagnosis notes",
                    diagnosis="Suspected Angina",
                    treatment_plan="Observe in OPD"
                ),
                db=s,
                current_user=u_da
            )

            # Doctor B attempts to read Doctor A's draft -> 403
            doc_b_draft_blocked = False
            try:
                get_consultation_draft(appointment_id=app_id, db=s, current_user=u_db)
            except HTTPException as he:
                if he.status_code == 403:
                    doc_b_draft_blocked = True

            # Patient A attempts to read Doctor A's unpublished draft -> 403
            patient_draft_blocked = False
            try:
                get_consultation_draft(appointment_id=app_id, db=s, current_user=u_pa)
            except HTTPException as he:
                if he.status_code == 403:
                    patient_draft_blocked = True

            # Doctor A reads own draft -> 200
            draft_res = get_consultation_draft(appointment_id=app_id, db=s, current_user=u_da)
            doc_a_draft_allowed = (draft_res.get("diagnosis") == "Suspected Angina")

        passed = doc_b_draft_blocked and patient_draft_blocked and doc_a_draft_allowed
        record_check(6, "Doctor Consultation Draft Isolation", passed,
                     f"Other doctor blocked={doc_b_draft_blocked}, Patient blocked={patient_draft_blocked}, Assigned doc allowed={doc_a_draft_allowed}")
    except Exception as e:
        record_check(6, "Doctor Consultation Draft Isolation", False, str(e))

    # --------------------------------------------------------------------------
    # Check 7: Duplicate Consultation Finalization Prevention
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            u_da = s.query(UserModel).filter(UserModel.id == "usr-doc-A").first()
            app_id = opd_a["id"]

            # 7a. Doctor A finalizes consultation -> 200 OK
            first_final = record_consultation(
                payload=ConsultationCreateRequest(
                    appointment_id=app_id,
                    clinical_notes="Finalized notes: Sinus rhythm confirmed.",
                    diagnosis="Mild Palpitations",
                    treatment_plan="Reassurance and oral hydration"
                ),
                db=s,
                current_user=u_da
            )
            first_success = (first_final.get("status") == "COMPLETED")

            # 7b. Duplicate finalization attempt -> 409 Conflict
            duplicate_blocked = False
            try:
                record_consultation(
                    payload=ConsultationCreateRequest(
                        appointment_id=app_id,
                        clinical_notes="Duplicate attempt",
                        diagnosis="Duplicate",
                        treatment_plan="Duplicate"
                    ),
                    db=s,
                    current_user=u_da
                )
            except HTTPException as he:
                if he.status_code == 409:
                    duplicate_blocked = True

        passed = first_success and duplicate_blocked
        record_check(7, "Consultation Finalization Duplicate Guard", passed,
                     f"First finalization succeeded={first_success}, Duplicate rejected with 409={duplicate_blocked}")
    except Exception as e:
        record_check(7, "Consultation Finalization Duplicate Guard", False, str(e))

    # --------------------------------------------------------------------------
    # Check 8: Concurrent Booking Slot Collision Guard (Multithreaded)
    # --------------------------------------------------------------------------
    try:
        # Patient A and Patient B concurrently attempt to book the exact same slot on doc-A
        with Session() as s:
            u_pa = s.query(UserModel).filter(UserModel.id == "usr-pat-A").first()
            u_pb = s.query(UserModel).filter(UserModel.id == "usr-pat-B").first()

        race_results = []
        def book_race(patient_id, user_obj, worker_id):
            ws = Session()
            try:
                res = create_opd_appointment(
                    payload=OPDCreateRequest(
                        patient_id=patient_id,
                        hospital_id="hosp-A",
                        doctor_id="doc-A",
                        department="Cardiology",
                        appointment_date="2026-12-15",
                        appointment_time="03:30 PM"
                    ),
                    db=ws,
                    current_user=user_obj
                )
                race_results.append((worker_id, 200, res.get("reference_id")))
            except HTTPException as he:
                race_results.append((worker_id, he.status_code, he.detail))
            finally:
                ws.close()

        # Launch 6 concurrent attempts (3 for Pat A, 3 for Pat B)
        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=book_race, args=("pat-A", u_pa, f"A-{i}")))
            threads.append(threading.Thread(target=book_race, args=("pat-B", u_pb, f"B-{i}")))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in race_results if r[1] == 200]
        conflicts = [r for r in race_results if r[1] == 409]

        with Session() as s:
            db_slots = s.query(OPDAppointmentModel).filter(
                OPDAppointmentModel.active_slot_lock == "doc-A#2026-12-15#03:30 PM"
            ).all()

        passed = (len(successes) == 1) and (len(conflicts) == 5) and (len(db_slots) == 1)
        record_check(8, "Concurrent Multi-User Booking Collision Guard (6 Threads)", passed,
                     f"Successes={len(successes)}, Conflicts={len(conflicts)}, Confirmed in DB={len(db_slots)}")
    except Exception as e:
        record_check(8, "Concurrent Multi-User Booking Collision Guard (6 Threads)", False, str(e))

    # --------------------------------------------------------------------------
    # Check 9: Active Database Zero-Mutation Guarantee
    # --------------------------------------------------------------------------
    try:
        active_conn2 = sqlite3.connect(active_db)
        active_cur2 = active_conn2.cursor()
        active_cur2.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        post_tables = active_cur2.fetchone()[0]
        active_cur2.execute("SELECT count(*) FROM users;")
        post_users = active_cur2.fetchone()[0]
        active_conn2.close()

        passed = (active_tables_count == post_tables) and (active_users_count == post_users)
        record_check(9, "Active Production Database Zero-Mutation Guarantee (chikitsax.db untouched)", passed,
                     f"Tables before={active_tables_count}, after={post_tables}; Users before={active_users_count}, after={post_users}")
    except Exception as e:
        record_check(9, "Active Production Database Zero-Mutation Guarantee (chikitsax.db untouched)", False, str(e))

    # Cleanup test files & DB
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    synth_file = os.path.join(CURRENT_DIR, "uploads", "medical_records", "test_synth_record_A.txt")
    if os.path.exists(synth_file):
        try:
            os.remove(synth_file)
        except Exception:
            pass

    print("=" * 80)
    all_passed = all(r[2] == "PASS" for r in results)
    if all_passed:
        print(f"ALL {len(results)} MULTI-USER AUDIT CHECKS PASSED (100%)!")
    else:
        print(f"FAILURES DETECTED: {[r for r in results if r[2] != 'PASS']}")
    print("=" * 80)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_tests())
