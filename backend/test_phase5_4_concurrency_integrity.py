"""
CHIKITSA-X - Phase 5.4 Database Integrity, Concurrency & Production Readiness Test Suite
Verifies:
1. Foreign-key constraint enforcement (PRAGMA foreign_keys=ON).
2. Server-controlled care_stage integrity (rejection of arbitrary client jumps/regressions).
3. Monotonic workflow progression milestones (stages 1 -> 2 -> 3 -> 4 -> 6 -> 7 -> 8 -> 9 -> 11).
4. Concurrent appointment booking race conditions (10 threads, exactly 1 wins, 9 get 409).
5. Concurrent slot rescheduling collision detection.
6. Consultation finalization concurrency and duplicate prevention.
7. Backup and restore integrity verification.
8. Active database zero-mutation verification.

Executed against an ISOLATED test database (chikitsax.db untouched).
"""

import os
import sys
import shutil
import sqlite3
import threading
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import Base, apply_safe_migrations, DEFAULT_DB_FILE
from app.seed import seed_database
from app.auth import create_access_token
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.hospital import HospitalModel
from app.models.opd import OPDAppointmentModel
from app.models.qr import QRReferenceModel
from app.models.consultation import ConsultationModel
from app.models.financial import TreatmentCostEstimateModel, CareToCostAssessmentModel
from app.schemas import (
    OPDCreateRequest,
    OPDRescheduleRequest,
    ConsultationCreateRequest,
    PatientProfileUpdate,
    HospitalVerifyRequest,
    TreatmentEstimateCreateRequest,
    IntakeRequest,
    TriageRequest,
    MedicalRecordCreate,
    FinancialAssessmentRequest
)
from app.routers.opd import create_opd_appointment, reschedule_opd_appointment
from app.routers.consultations import record_consultation
from app.routers.patients import update_patient
from app.routers.qr import hospital_staff_verify
from app.routers.financial import create_treatment_cost_estimate, assess_care_to_cost
from app.routers.intake import submit_intake
from app.routers.triage import perform_triage
from app.routers.medical_records import upload_medical_record

TEST_DB_PATH = os.path.join(CURRENT_DIR, "test_isolated_phase5_4.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.replace(os.sep, '/')}"

def run_tests():
    print("=" * 80)
    print("CHIKITSA-X PHASE 5.4: DATABASE INTEGRITY & CONCURRENCY TEST SUITE")
    print("=" * 80)

    # Record active DB baseline
    active_db = DEFAULT_DB_FILE
    active_conn = sqlite3.connect(active_db)
    active_cur = active_conn.cursor()
    active_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    active_tables_count = active_cur.fetchone()[0]
    active_cur.execute("SELECT count(*) FROM users;")
    active_users_count = active_cur.fetchone()[0]
    active_conn.close()

    # Clean isolated DB if exists
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    apply_safe_migrations(engine)
    Session = sessionmaker(bind=engine)

    # Seed isolated DB
    with Session() as s:
        seed_database(s)

    results = []

    def record_check(num: int, title: str, passed: bool, msg: str = ""):
        status_str = "PASS" if passed else "FAIL"
        results.append((num, title, status_str, msg))
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"{icon} Check {num}: {title} {('- ' + msg) if msg else ''}", flush=True)

    # --------------------------------------------------------------------------
    # Check 1: Foreign-Key Enforcement (PRAGMA foreign_keys=ON)
    # --------------------------------------------------------------------------
    try:
        with engine.connect() as conn:
            fk_status = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        
        # Test inserting an appointment with non-existent hospital and doctor
        fk_failed_as_expected = False
        with Session() as s:
            invalid_opd = OPDAppointmentModel(
                id="opd-fk-test",
                reference_id="CHX-FK-TEST",
                patient_id="usr-patient-1",
                patient_name="Test Patient",
                patient_phone="1234567890",
                hospital_id="non-existent-hosp-999",
                hospital_name="Ghost Hospital",
                department="Cardiology",
                doctor_id="non-existent-doc-999",
                doctor_name="Ghost Doctor",
                appointment_date="2026-12-01",
                appointment_time="10:00 AM",
                status="CONFIRMED"
            )
            s.add(invalid_opd)
            try:
                s.commit()
            except IntegrityError:
                s.rollback()
                fk_failed_as_expected = True

        passed = (fk_status == 1) and fk_failed_as_expected
        record_check(1, "Foreign-Key Enforcement Active & Blocks Invalid Foreign Keys", passed,
                     f"PRAGMA foreign_keys={fk_status}, FK constraint blocked invalid reference={fk_failed_as_expected}")
    except Exception as e:
        record_check(1, "Foreign-Key Enforcement Active & Blocks Invalid Foreign Keys", False, str(e))

    # --------------------------------------------------------------------------
    # Check 2: Patient Care-Stage Client Tamper Protection
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            pat = s.query(PatientModel).filter(PatientModel.user_id == "usr-patient-1").first()
            user_pat = s.query(UserModel).filter(UserModel.id == "usr-patient-1").first()
            orig_stage = pat.care_stage

            # 2a. Attempt arbitrary forward jump to stage 11
            jump_blocked = False
            try:
                update_patient(
                    patient_id=pat.id,
                    payload=PatientProfileUpdate(careStage=11),
                    db=s,
                    current_user=user_pat
                )
            except HTTPException as he:
                if he.status_code == 400 and "Arbitrary care_stage modification is forbidden" in he.detail:
                    jump_blocked = True

            # 2b. Attempt regression to stage 1
            regression_blocked = False
            try:
                update_patient(
                    patient_id=pat.id,
                    payload=PatientProfileUpdate(careStage=1),
                    db=s,
                    current_user=user_pat
                )
            except HTTPException as he:
                if he.status_code == 400 and "Arbitrary care_stage modification is forbidden" in he.detail:
                    regression_blocked = True

            # 2c. Allow legitimate demographic update
            demo_updated = False
            res = update_patient(
                patient_id=pat.id,
                payload=PatientProfileUpdate(fullName="Ramesh Sharma Updated", bloodGroup="AB+"),
                db=s,
                current_user=user_pat
            )
            if res.get("fullName") == "Ramesh Sharma Updated" and res.get("careStage") == orig_stage:
                demo_updated = True

        passed = jump_blocked and regression_blocked and demo_updated
        record_check(2, "Patient Care-Stage Tamper Protection", passed,
                     f"Jump blocked={jump_blocked}, Regression blocked={regression_blocked}, Demographic update allowed={demo_updated}")
    except Exception as e:
        record_check(2, "Patient Care-Stage Tamper Protection", False, str(e))

    # --------------------------------------------------------------------------
    # Check 3: Monotonic Clinical Workflow Progression Across All Milestones
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            # Create a brand new patient at stage 1
            p_user = UserModel(id="usr-prog-1", email="prog@chikitsax.test", password_hash="hash", name="Prog Test", role="PATIENT")
            s.add(p_user)
            s.flush()
            p_profile = PatientModel(id="pat-prog-1", user_id="usr-prog-1", full_name="Prog Test", age=30, gender="Male",
                                     blood_group="O+", phone="9999988888", email="prog@chikitsax.test", address="Addr",
                                     city="Pune", pincode="411001", care_stage=1)
            s.add(p_profile)
            s.commit()

            stages = [p_profile.care_stage] # Stage 1

            # Step 1 -> 2: Symptom Intake
            submit_intake(IntakeRequest(patientId="pat-prog-1", rawTranscript="Patient reports severe palpitations"), db=s, current_user=p_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 2 -> 3: Medical Record Upload
            upload_medical_record(MedicalRecordCreate(
                patient_id="pat-prog-1",
                file_name="cardio_report.pdf",
                file_type="application/pdf",
                category="Lab Report",
                extractedData={}
            ), db=s, current_user=p_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 3 -> 4: AI Triage
            perform_triage(TriageRequest(patientId="pat-prog-1", symptoms=["Palpitations", "Shortness of breath"]), db=s, current_user=p_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 4 -> 6: OPD Appointment Booking
            opd_res = create_opd_appointment(OPDCreateRequest(
                patient_id="pat-prog-1",
                hospital_id="hosp-1",
                doctor_id="doc-1",
                department="Cardiology",
                appointment_date="2026-12-10",
                appointment_time="11:30 AM"
            ), db=s, current_user=p_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 6 -> 7: Hospital Check-in Verification
            hosp_admin = s.query(UserModel).filter(UserModel.role == "HOSPITAL_ADMIN").first()
            hospital_staff_verify(HospitalVerifyRequest(reference_id=opd_res["reference_id"], hospital_id="hosp-1"), db=s, current_user=hosp_admin)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 7 -> 8: Doctor Consultation Finalization
            doc_user = s.query(UserModel).filter(UserModel.id == "usr-doctor-1").first()
            record_consultation(ConsultationCreateRequest(
                appointment_id=opd_res["id"],
                clinical_notes="Patient examined. ECG shows sinus rhythm with occasional PACs.",
                diagnosis="Cardiac Arrhythmia (Mild)",
                treatment_plan="Lifestyle modification and low dose beta blockers."
            ), db=s, current_user=doc_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 8 -> 9: Treatment Cost Estimate
            create_treatment_cost_estimate(TreatmentEstimateCreateRequest(
                patient_id="pat-prog-1",
                procedure_name="Diagnostic Angiography",
                estimated_cost_min=25000,
                estimated_cost_max=45000
            ), db=s, current_user=doc_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Step 9 -> 11: Care-to-Cost Affordability Assessment
            assess_care_to_cost(FinancialAssessmentRequest(
                patient_id="pat-prog-1",
                treatment_cost=35000,
                insurance_coverage=30000
            ), db=s, current_user=p_user)
            s.refresh(p_profile)
            stages.append(p_profile.care_stage)

            # Monotonicity test: repeating intake must NOT regress stage back to 2
            submit_intake(IntakeRequest(patientId="pat-prog-1", rawTranscript="Followup check"), db=s, current_user=p_user)
            s.refresh(p_profile)
            final_stage = p_profile.care_stage

        expected_sequence = [1, 2, 3, 4, 6, 7, 8, 9, 11]
        passed = (stages == expected_sequence) and (final_stage == 11)
        record_check(3, "Monotonic Clinical Workflow Progression Across Milestones", passed,
                     f"Recorded sequence={stages}, Final non-regressed stage={final_stage}")
    except Exception as e:
        record_check(3, "Monotonic Clinical Workflow Progression Across Milestones", False, str(e))

    # --------------------------------------------------------------------------
    # Check 4: Multithreaded Concurrent Booking Race Condition & Collision Guard
    # --------------------------------------------------------------------------
    try:
        concurrent_results = []
        def concurrent_book_worker(worker_id):
            worker_session = Session()
            try:
                req = OPDCreateRequest(
                    patient_id="usr-patient-1",
                    hospital_id="hosp-1",
                    doctor_id="doc-1",
                    department="Cardiology",
                    appointment_date="2026-12-25",
                    appointment_time="02:00 PM"
                )
                res = create_opd_appointment(req, db=worker_session, current_user=None)
                concurrent_results.append((worker_id, 200, res.get("reference_id") or res.get("referenceId")))
            except HTTPException as he:
                concurrent_results.append((worker_id, he.status_code, he.detail))
            finally:
                worker_session.close()

        threads = [threading.Thread(target=concurrent_book_worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in concurrent_results if r[1] == 200]
        conflicts = [r for r in concurrent_results if r[1] == 409]

        with Session() as s:
            slot_lock = "doc-1#2026-12-25#02:00 PM"
            db_appointments = s.query(OPDAppointmentModel).filter(
                OPDAppointmentModel.active_slot_lock == slot_lock
            ).all()

        passed = (len(successes) == 1) and (len(conflicts) == 9) and (len(db_appointments) == 1)
        record_check(4, "Concurrent Booking Race Condition Guard (10 Threads)", passed,
                     f"Successes={len(successes)}, Conflicts={len(conflicts)}, DB records={len(db_appointments)}")
    except Exception as e:
        record_check(4, "Concurrent Booking Race Condition Guard (10 Threads)", False, str(e))

    # --------------------------------------------------------------------------
    # Check 5: Concurrent Slot Rescheduling Collision Guard
    # --------------------------------------------------------------------------
    try:
        # Create 2 distinct initial appointments
        with Session() as s:
            app1 = OPDAppointmentModel(
                id="opd-resched-1",
                reference_id="CHX-RESCHED-1",
                patient_id="usr-patient-1",
                patient_name="Patient 1",
                patient_phone="+91 98765 43210",
                hospital_id="hosp-1",
                hospital_name="CarePlus Super Specialty Hospital",
                doctor_id="doc-1",
                doctor_name="Dr. Rajesh Kulkarni",
                department="Cardiology",
                appointment_date="2026-12-28",
                appointment_time="09:00 AM",
                active_slot_lock="doc-1#2026-12-28#09:00 AM",
                status="CONFIRMED",
                qr_token="TOKEN_RESCHED_1"
            )
            app2 = OPDAppointmentModel(
                id="opd-resched-2",
                reference_id="CHX-RESCHED-2",
                patient_id="pat-prog-1",
                patient_name="Patient 2",
                patient_phone="+91 99999 88888",
                hospital_id="hosp-1",
                hospital_name="CarePlus Super Specialty Hospital",
                doctor_id="doc-1",
                doctor_name="Dr. Rajesh Kulkarni",
                department="Cardiology",
                appointment_date="2026-12-28",
                appointment_time="10:00 AM",
                active_slot_lock="doc-1#2026-12-28#10:00 AM",
                status="CONFIRMED",
                qr_token="TOKEN_RESCHED_2"
            )
            s.add(app1)
            s.add(app2)
            s.commit()

        with Session() as s:
            user1 = s.query(UserModel).filter(UserModel.id == "usr-patient-1").first()
            user2 = s.query(UserModel).filter(UserModel.id == "usr-prog-1").first()

        # Concurrently reschedule both to 2026-12-28 11:00 AM
        resched_results = []
        def resched_worker(app_id, req_user, worker_id):
            ws = Session()
            try:
                res = reschedule_opd_appointment(
                    appointment_id=app_id,
                    payload=OPDRescheduleRequest(
                        appointment_date="2026-12-28",
                        appointment_time="11:00 AM"
                    ),
                    db=ws,
                    current_user=req_user
                )
                resched_results.append((worker_id, 200, res.get("reference_id") or res.get("id")))
            except HTTPException as he:
                resched_results.append((worker_id, he.status_code, he.detail))
            finally:
                ws.close()

        t1 = threading.Thread(target=resched_worker, args=("opd-resched-1", user1, 1))
        t2 = threading.Thread(target=resched_worker, args=("opd-resched-2", user2, 2))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        r_succ = [r for r in resched_results if r[1] == 200]
        r_conf = [r for r in resched_results if r[1] == 409]

        passed = (len(r_succ) == 1) and (len(r_conf) == 1)
        record_check(5, "Concurrent Slot Rescheduling Collision Guard", passed,
                     f"Successes={len(r_succ)}, Conflicts={len(r_conf)}")
    except Exception as e:
        record_check(5, "Concurrent Slot Rescheduling Collision Guard", False, str(e))

    # --------------------------------------------------------------------------
    # Check 6: Consultation Finalization Concurrency & Duplicate Prevention
    # --------------------------------------------------------------------------
    try:
        with Session() as s:
            cons_app = OPDAppointmentModel(
                id="opd-cons-race",
                reference_id="CHX-CONS-RACE",
                patient_id="usr-patient-1",
                patient_name="Ramesh Sharma",
                patient_phone="+91 98765 43210",
                hospital_id="hosp-1",
                hospital_name="CarePlus Super Specialty Hospital",
                doctor_id="doc-1",
                doctor_name="Dr. Rajesh Kulkarni",
                department="Cardiology",
                appointment_date="2026-12-30",
                appointment_time="10:00 AM",
                active_slot_lock="doc-1#2026-12-30#10:00 AM",
                status="CONFIRMED",
                qr_token="TOKEN_CONS_RACE"
            )
            s.add(cons_app)
            s.commit()

        doc_user = None
        with Session() as s:
            doc_user = s.query(UserModel).filter(UserModel.id == "usr-doctor-1").first()

        cons_results = []
        def cons_worker(worker_id):
            ws = Session()
            try:
                res = record_consultation(
                    ConsultationCreateRequest(
                        appointment_id="opd-cons-race",
                        clinical_notes="Concurrent test notes",
                        diagnosis="Hypertension",
                        treatment_plan="Daily monitoring"
                    ),
                    db=ws,
                    current_user=doc_user
                )
                cons_results.append((worker_id, 200, res.get("id")))
            except HTTPException as he:
                cons_results.append((worker_id, he.status_code, he.detail))
            finally:
                ws.close()

        c_threads = [threading.Thread(target=cons_worker, args=(i,)) for i in range(5)]
        for ct in c_threads:
            ct.start()
        for ct in c_threads:
            ct.join()

        c_succ = [r for r in cons_results if r[1] == 200]
        c_conf = [r for r in cons_results if r[1] == 409]

        with Session() as s:
            final_cons_count = s.query(ConsultationModel).filter(
                ConsultationModel.appointment_id == "opd-cons-race"
            ).count()

        passed = (len(c_succ) == 1) and (len(c_conf) == 4) and (final_cons_count == 1)
        record_check(6, "Consultation Finalization Concurrency & Duplicate Guard (5 Threads)", passed,
                     f"Successes={len(c_succ)}, Conflicts={len(c_conf)}, Final records in DB={final_cons_count}")
    except Exception as e:
        record_check(6, "Consultation Finalization Concurrency & Duplicate Guard (5 Threads)", False, str(e))

    # --------------------------------------------------------------------------
    # Check 7: Backup & Restore Integrity Verification
    # --------------------------------------------------------------------------
    try:
        backup_file = os.path.join(CURRENT_DIR, "chikitsax_backup_phase5_4_20261031_233800.db")
        restore_verify_db = os.path.join(CURRENT_DIR, "test_restore_verify.db")
        if os.path.exists(restore_verify_db):
            os.remove(restore_verify_db)

        # Restore from backup to test file
        shutil.copy2(backup_file, restore_verify_db)

        # Verify restored DB integrity
        r_conn = sqlite3.connect(restore_verify_db)
        r_cur = r_conn.cursor()
        r_cur.execute("PRAGMA integrity_check;")
        integrity = r_cur.fetchone()[0]

        # Verify table counts match backup
        b_conn = sqlite3.connect(backup_file)
        b_cur = b_conn.cursor()
        b_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        b_tables = b_cur.fetchone()[0]
        r_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        r_tables = r_cur.fetchone()[0]

        b_cur.execute("SELECT count(*) FROM users;")
        b_users = b_cur.fetchone()[0]
        r_cur.execute("SELECT count(*) FROM users;")
        r_users = r_cur.fetchone()[0]

        r_conn.close()
        b_conn.close()

        if os.path.exists(restore_verify_db):
            os.remove(restore_verify_db)

        passed = (integrity == "ok") and (b_tables == r_tables) and (b_users == r_users)
        record_check(7, "Backup & Restore Integrity Verification", passed,
                     f"PRAGMA integrity_check={integrity}, Tables={r_tables}/{b_tables}, Users={r_users}/{b_users}")
    except Exception as e:
        record_check(7, "Backup & Restore Integrity Verification", False, str(e))

    # --------------------------------------------------------------------------
    # Check 8: Active Database Zero-Mutation Verification
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
        record_check(8, "Active Database Zero-Mutation Guarantee (chikitsax.db untouched)", passed,
                     f"Tables before={active_tables_count}, after={post_tables}; Users before={active_users_count}, after={post_users}")
    except Exception as e:
        record_check(8, "Active Database Zero-Mutation Guarantee (chikitsax.db untouched)", False, str(e))

    # Cleanup isolated test DB
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    print("=" * 80)
    all_passed = all(r[2] == "PASS" for r in results)
    if all_passed:
        print(f"ALL {len(results)} CHECKS PASSED SUCCESSFULLY!")
    else:
        print(f"FAILURES DETECTED: {[r for r in results if r[2] != 'PASS']}")
    print("=" * 80)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_tests())
