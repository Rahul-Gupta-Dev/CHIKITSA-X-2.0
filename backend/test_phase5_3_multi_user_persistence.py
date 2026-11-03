"""
CHIKITSA-X - Phase 5.3 Multi-User Persistence & Mock Elimination Test Suite
Verifies all Phase 5.3 backend persistence, mock elimination, and multi-user authorization
checks against an ISOLATED test database (chikitsax.db untouched).
"""

import os
import sys
import io
import json
import base64
import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.main import app
from app.database import Base, get_db as db_get_db, apply_safe_migrations, DEFAULT_DB_FILE
from app.auth import get_db as auth_get_db, create_access_token
from app.seed import seed_database
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.hospital import HospitalModel, HospitalReviewModel
from app.models.opd import OPDAppointmentModel
from app.models.consultation import ConsultationModel, ConsultationDraftModel
from app.models.medical_record import MedicalRecordModel
from fastapi.testclient import TestClient

import threading

TEST_DB_PATH = os.path.join(CURRENT_DIR, "test_isolated_phase5_3.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.replace(os.sep, '/')}"

def _start_timeout_watchdog(timeout_sec: int = 60) -> threading.Timer:
    def _on_timeout():
        print(f"\n[DIAGNOSTIC TIMEOUT] Test suite timed out after {timeout_sec}s!", file=sys.stderr, flush=True)
        print("[DIAGNOSTIC TIMEOUT] Process blocked waiting on I/O or loopback socket communication.", file=sys.stderr, flush=True)
        os._exit(124)
    timer = threading.Timer(timeout_sec, _on_timeout)
    timer.daemon = True
    timer.start()
    return timer

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

    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    return engine, TestingSessionLocal

def run_tests():
    watchdog = _start_timeout_watchdog(timeout_sec=60)
    print("=" * 80, flush=True)
    print("CHIKITSA-X - Phase 5.3 Multi-User Persistence & Mock Elimination Tests", flush=True)
    print("=" * 80, flush=True)
    print(f"Isolated Test Database: {TEST_DB_PATH}", flush=True)
    print(f"Active Production Database (Protected): {DEFAULT_DB_FILE}", flush=True)
    print("-" * 80, flush=True)

    active_db_before_stat = os.stat(DEFAULT_DB_FILE) if os.path.exists(DEFAULT_DB_FILE) else None

    engine, TestingSessionLocal = setup_isolated_test_db()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_get_db] = override_get_db
    app.dependency_overrides[auth_get_db] = override_get_db

    client = TestClient(app)
    results = []

    def record_check(num: int, title: str, passed: bool, msg: str = ""):
        status_str = "PASS" if passed else "FAIL"
        results.append((num, title, status_str, msg))
        icon = "✅" if passed else "❌"
        print(f"{icon} Check {num}: {title} [{status_str}] {('- ' + msg) if msg else ''}", flush=True)
        if not passed:
            raise AssertionError(f"Check {num} FAILED: {msg}")

    try:
        # 1. Base Logins
        p1_login = client.post("/api/auth/login", json={"email": "patient@chikitsax.demo", "password": "demo123", "role": "PATIENT"})
        assert p1_login.status_code == 200, f"Patient login failed: {p1_login.json()}"
        p1_token = p1_login.json()["accessToken"]

        d1_login = client.post("/api/auth/login", json={"email": "doctor@chikitsax.demo", "password": "demo123", "role": "DOCTOR"})
        assert d1_login.status_code == 200, f"Doctor login failed: {d1_login.json()}"
        d1_token = d1_login.json()["accessToken"]

        # Doctor 2 token (unassigned doctor)
        with TestingSessionLocal() as s:
            u_doc2 = s.query(UserModel).filter(UserModel.id == "usr-doctor-2").first()
            if not u_doc2:
                u_doc2 = UserModel(
                    id="usr-doctor-2",
                    email="doctor2@chikitsax.demo",
                    name="Dr. Priya Deshmukh",
                    role="DOCTOR",
                    hospital_id="hosp-2"
                )
                s.add(u_doc2)
                s.commit()
            d2_token = create_access_token({"sub": u_doc2.id, "email": u_doc2.email, "role": "DOCTOR", "name": u_doc2.name})

        # ---------------------------------------------------------------------
        # Check 1: Medical Record OCR - Honest Extraction (No Fabricated Data)
        # ---------------------------------------------------------------------
        # Text file with genuine prescription text
        real_text_file = io.BytesIO(b"Dr. Rajesh Kulkarni\nCarePlus Hospital\nDiagnosis: Hypertension Evaluation\nTab Telmisartan 40mg OD\nTab Metformin 500mg BD")
        res_real = client.post(
            "/api/medical-records/upload",
            headers={"Authorization": f"Bearer {p1_token}"},
            data={"patient_id": "usr-patient-1", "category": "Prescription"},
            files={"file": ("real_rx.txt", real_text_file, "text/plain")}
        )
        assert res_real.status_code == 200, f"Real OCR upload failed: {res_real.json()}"
        ocr_real = res_real.json().get("ocr_extracted_data", {})
        has_real_meds = len(ocr_real.get("medicinesExtracted", [])) > 0

        # Binary file without OCR text
        binary_file = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01")
        res_bin = client.post(
            "/api/medical-records/upload",
            headers={"Authorization": f"Bearer {p1_token}"},
            data={"patient_id": "usr-patient-1", "category": "Lab Report"},
            files={"file": ("scan.png", binary_file, "image/png")}
        )
        assert res_bin.status_code == 200, f"Binary upload failed: {res_bin.json()}"
        ocr_bin = res_bin.json().get("ocr_extracted_data", {})
        # Must NOT fabricate fake medicines or fake lab values
        no_hallucinations = (
            len(ocr_bin.get("medicinesExtracted", [])) == 0 and
            len(ocr_bin.get("labResults", [])) == 0 and
            ocr_bin.get("ocrAdapterStatus") == "PENDING_MANUAL_REVIEW"
        )
        check1_pass = has_real_meds and no_hallucinations
        record_check(1, "Medical record upload extracts real text & never fabricates fake clinical data", check1_pass,
                     f"Real meds: {ocr_real.get('medicinesExtracted')}, Binary meds count: {len(ocr_bin.get('medicinesExtracted', []))}")

        # ---------------------------------------------------------------------
        # Check 2: Medical Record OCR Authorization Guards
        # ---------------------------------------------------------------------
        # Anonymous upload rejected
        anon_upload = client.post("/api/medical-records/upload", files={"file": ("test.png", io.BytesIO(b"data"), "image/png")})
        # Unassigned doctor upload without consent/appointment rejected
        doc2_upload = client.post(
            "/api/medical-records/upload",
            headers={"Authorization": f"Bearer {d2_token}"},
            data={"patient_id": "usr-patient-1", "category": "Prescription"},
            files={"file": ("test.png", io.BytesIO(b"data"), "image/png")}
        )
        check2_pass = (anon_upload.status_code == 401) and (doc2_upload.status_code == 403)
        record_check(2, "Medical record upload enforces authentication & doctor-patient relationship", check2_pass,
                     f"Anon status: {anon_upload.status_code}, Unassigned doctor status: {doc2_upload.status_code}")

        # ---------------------------------------------------------------------
        # Check 3: Financial Plan - Authenticated Server Calculation & Validation
        # ---------------------------------------------------------------------
        anon_plan = client.post("/api/financial/finance-plan", json={"treatment_cost": 100000})
        neg_plan = client.post("/api/financial/finance-plan", headers={"Authorization": f"Bearer {p1_token}"}, json={"treatment_cost": -500})
        valid_plan = client.post(
            "/api/financial/finance-plan",
            headers={"Authorization": f"Bearer {p1_token}"},
            json={
                "treatment_cost": 150000,
                "insurance_coverage": 60000,
                "government_support": 50000,
                "ngo_support": 25000,
                "additional_savings": 15000
            }
        )
        v_json = valid_plan.json()
        check3_pass = (
            anon_plan.status_code == 401 and
            neg_plan.status_code == 400 and
            valid_plan.status_code == 200 and
            v_json.get("remainingGap") == 0.0 and
            "100% COVERED" in v_json.get("recommendationTag", "")
        )
        record_check(3, "Financial plan uses authenticated server calculation without mock fallback", check3_pass,
                     f"Anon: {anon_plan.status_code}, Negative: {neg_plan.status_code}, Valid remaining gap: {v_json.get('remainingGap')}")

        # ---------------------------------------------------------------------
        # Check 4: Doctor Consultation Draft - Save & Retrieval
        # ---------------------------------------------------------------------
        # Find an active appointment assigned to doc-1
        with TestingSessionLocal() as s:
            app_draft = s.query(OPDAppointmentModel).filter(
                OPDAppointmentModel.doctor_id == "doc-1",
                OPDAppointmentModel.status == "CONFIRMED"
            ).first()
            if not app_draft:
                app_draft = OPDAppointmentModel(
                    id="opd-draft-test-1",
                    reference_id="CHX-DRAFT-1",
                    patient_id="usr-patient-1",
                    patient_name="Ramesh Sharma",
                    patient_phone="+91 98765 43210",
                    hospital_id="hosp-1",
                    hospital_name="CarePlus Hospital",
                    department="Cardiology",
                    doctor_id="doc-1",
                    doctor_name="Dr. Rajesh Kulkarni",
                    appointment_date="2026-11-15",
                    appointment_time="10:00 AM",
                    status="CONFIRMED"
                )
                s.add(app_draft)
                s.commit()
            target_app_id = app_draft.id

        draft_payload = {
            "appointment_id": target_app_id,
            "clinical_notes": "Patient complains of chest tightness upon exertion. Vitals stable.",
            "diagnosis": "Suspected Angina Pectoris",
            "treatment_plan": "Schedule Stress Echo. Restrict high-sodium diet.",
            "prescription_medicines": [{"name": "Aspirin 75mg", "dosage": "1-0-0", "duration": "30 days"}]
        }

        save_draft_res = client.post(
            "/api/consultations/draft",
            headers={"Authorization": f"Bearer {d1_token}"},
            json=draft_payload
        )
        get_draft_res = client.get(
            f"/api/consultations/draft/{target_app_id}",
            headers={"Authorization": f"Bearer {d1_token}"}
        )
        draft_json = get_draft_res.json()
        check4_pass = (
            save_draft_res.status_code == 200 and
            get_draft_res.status_code == 200 and
            draft_json.get("diagnosis") == "Suspected Angina Pectoris" and
            len(draft_json.get("prescriptionMedicines", [])) == 1
        )
        record_check(4, "Doctor consultation draft persists and restores accurately on server", check4_pass,
                     f"Save status: {save_draft_res.status_code}, Saved Diagnosis: {draft_json.get('diagnosis')}")

        # ---------------------------------------------------------------------
        # Check 5: Doctor Consultation Draft - Authorization Protection
        # ---------------------------------------------------------------------
        # Patient cannot save or view doctor draft
        pat_draft_save = client.post("/api/consultations/draft", headers={"Authorization": f"Bearer {p1_token}"}, json=draft_payload)
        pat_draft_get = client.get(f"/api/consultations/draft/{target_app_id}", headers={"Authorization": f"Bearer {p1_token}"})
        # Unassigned doctor cannot view draft
        doc2_draft_get = client.get(f"/api/consultations/draft/{target_app_id}", headers={"Authorization": f"Bearer {d2_token}"})
        # Anon cannot view draft
        anon_draft_get = client.get(f"/api/consultations/draft/{target_app_id}")

        check5_pass = (
            pat_draft_save.status_code == 403 and
            pat_draft_get.status_code == 403 and
            doc2_draft_get.status_code == 403 and
            anon_draft_get.status_code == 401
        )
        record_check(5, "Consultation draft strictly restricted to assigned doctor", check5_pass,
                     f"Patient save: {pat_draft_save.status_code}, Patient get: {pat_draft_get.status_code}, Other doc: {doc2_draft_get.status_code}, Anon: {anon_draft_get.status_code}")

        # ---------------------------------------------------------------------
        # Check 6: Consultation Finalization Deletes Draft & Locks Against Overwrites
        # ---------------------------------------------------------------------
        finalize_res = client.post(
            "/api/consultations",
            headers={"Authorization": f"Bearer {d1_token}"},
            json={
                "appointment_id": target_app_id,
                "clinical_notes": "Finalized notes: Angina controlled.",
                "diagnosis": "Stable Angina Pectoris",
                "treatment_plan": "Continue medication as prescribed.",
                "prescription_medicines": [{"name": "Aspirin 75mg", "dosage": "1-0-0", "duration": "30 days"}]
            }
        )
        # Attempt to save draft again on finalized consultation -> must return 409 Conflict
        draft_after_final = client.post(
            "/api/consultations/draft",
            headers={"Authorization": f"Bearer {d1_token}"},
            json=draft_payload
        )
        # Attempt to finalize again -> must return 409 Conflict
        refinalize = client.post(
            "/api/consultations",
            headers={"Authorization": f"Bearer {d1_token}"},
            json={
                "appointment_id": target_app_id,
                "clinical_notes": "Trying to overwrite finalized record.",
                "diagnosis": "Overwritten",
                "treatment_plan": "Overwritten"
            }
        )
        # Verify draft was cleaned up in isolated test DB
        with TestingSessionLocal() as s:
            draft_in_db = s.query(ConsultationDraftModel).filter(ConsultationDraftModel.appointment_id == target_app_id).first()

        check6_pass = (
            finalize_res.status_code == 200 and
            draft_after_final.status_code == 409 and
            refinalize.status_code == 409 and
            draft_in_db is None
        )
        record_check(6, "Consultation finalization purges draft and prevents overwriting (409 Conflict)", check6_pass,
                     f"Finalize: {finalize_res.status_code}, Draft after final: {draft_after_final.status_code}, Refinalize: {refinalize.status_code}")

        # ---------------------------------------------------------------------
        # Check 7: Patient Intake Server Persistence
        # ---------------------------------------------------------------------
        intake_res = client.post(
            "/api/intake",
            headers={"Authorization": f"Bearer {p1_token}"},
            json={
                "patient_id": "usr-patient-1",
                "transcript": "Severe chest tightness and shortness of breath since yesterday evening.",
                "language": "en-IN"
            }
        )
        intake_json = intake_res.json()
        anon_intake = client.post(
            "/api/intake",
            json={"patient_id": "usr-patient-1", "transcript": "Fever"}
        )
        check7_pass = (
            intake_res.status_code == 200 and
            "id" in intake_json and
            len(intake_json.get("extracted_symptoms", [])) > 0 and
            anon_intake.status_code == 401
        )
        record_check(7, "Patient clinical intake securely persists to database and rejects unauthenticated requests", check7_pass,
                     f"Intake ID: {intake_json.get('id')}, Extracted: {intake_json.get('extracted_symptoms')}, Anon: {anon_intake.status_code}")

        # ---------------------------------------------------------------------
        # Check 8: Hospital Reviews - Patient Submission & Public Viewing
        # ---------------------------------------------------------------------
        review_res = client.post(
            "/api/hospitals/hosp-1/reviews",
            headers={"Authorization": f"Bearer {p1_token}"},
            json={
                "rating": 5.0,
                "review_text": "Exceptional cardiology facilities and prompt outpatient care."
            }
        )
        rev_json = review_res.json()
        public_reviews = client.get("/api/hospitals/hosp-1/reviews")
        pub_list = public_reviews.json()
        check8_pass = (
            review_res.status_code == 200 and
            rev_json.get("rating") == 5.0 and
            rev_json.get("patientName") == "Ramesh Sharma" and
            public_reviews.status_code == 200 and
            len(pub_list) >= 1
        )
        record_check(8, "Patient can submit verified hospital review and view public reviews", check8_pass,
                     f"Review ID: {rev_json.get('id')}, Rating: {rev_json.get('rating')}, Total Reviews: {len(pub_list)}")

        # ---------------------------------------------------------------------
        # Check 9: Hospital Reviews - Duplicate Update & Dynamic Aggregation
        # ---------------------------------------------------------------------
        # Patient updates their review to 4.0
        update_review = client.post(
            "/api/hospitals/hosp-1/reviews",
            headers={"Authorization": f"Bearer {p1_token}"},
            json={
                "rating": 4.0,
                "review_text": "Updated: Good facilities, but waiting room was somewhat crowded."
            }
        )
        # Check hospital model rating updated in DB
        with TestingSessionLocal() as s:
            hosp_db = s.query(HospitalModel).filter(HospitalModel.id == "hosp-1").first()
            h_rating = hosp_db.rating if hosp_db else None
            h_count = hosp_db.review_count if hosp_db else None

        check9_pass = (
            update_review.status_code == 200 and
            update_review.json().get("rating") == 4.0 and
            h_rating is not None and
            h_count == 1
        )
        record_check(9, "Repeated reviews by same patient update existing record & recalculate hospital average", check9_pass,
                     f"Updated rating: {update_review.json().get('rating')}, Hospital average: {h_rating}, Review count: {h_count}")

        # ---------------------------------------------------------------------
        # Check 10: Hospital Reviews - Authorization Guards (Non-patients & Anon rejected)
        # ---------------------------------------------------------------------
        anon_rev = client.post("/api/hospitals/hosp-1/reviews", json={"rating": 5.0, "review_text": "Great"})
        doc_rev = client.post("/api/hospitals/hosp-1/reviews", headers={"Authorization": f"Bearer {d1_token}"}, json={"rating": 5.0, "review_text": "Great"})
        check10_pass = (anon_rev.status_code == 401) and (doc_rev.status_code == 403)
        record_check(10, "Hospital review submissions reject anonymous and privileged non-patient roles", check10_pass,
                     f"Anon status: {anon_rev.status_code}, Doctor status: {doc_rev.status_code}")

        # ---------------------------------------------------------------------
        # Check 11: Production Database Zero-Mutation Verification
        # ---------------------------------------------------------------------
        conn = sqlite3.connect(DEFAULT_DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM consultations WHERE clinical_notes LIKE '%Finalized notes: Angina controlled%'")
        leak_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        conn.close()

        check11_pass = (leak_count == 0) and (integrity == "ok")
        record_check(11, "Active production database has zero test mutations & integrity ok", check11_pass,
                     f"Test consultation leakage: {leak_count}, Active DB integrity: {integrity}")

    finally:
        watchdog.cancel()
        app.dependency_overrides.clear()
        engine.dispose()
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception as e:
                print(f"Notice: Test DB cleanup: {e}")

    print("=" * 80)
    print("All 11 Phase 5.3 Multi-User Persistence & Mock Elimination Checks PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
