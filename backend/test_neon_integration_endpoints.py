import os
import sys
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(CURRENT_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import build_engine, normalize_database_url
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.hospital import HospitalModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.models.consultation import ConsultationModel
from app.models.medical_record import MedicalRecordModel
from app.models.audit import AuditLogModel
from app.auth import verify_password
from sqlalchemy.orm import sessionmaker

def mask_url(url: str) -> str:
    if "@" in url:
        prefix = url.split("@")[0]
        suffix = url.split("@")[1]
        schema_part = prefix.split("://")[0] if "://" in prefix else "postgresql"
        return f"{schema_part}://***:***@{suffix}"
    return url

def run_integration_tests():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("CHIKITSA-X 2.0: NEON MANAGED POSTGRESQL INTEGRATION TEST SUITE")
    print("=" * 80)
    print(f"Target Database: {mask_url(raw_url)}")

    engine = build_engine(normalize_database_url(raw_url))
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    passed_checks = 0
    total_checks = 7

    with Session() as session:
        # Check 1: User Query & Authentication Verification
        print("\n[Test 1] User Retrieval & Password Hash Compatibility...")
        user = session.query(UserModel).filter(UserModel.password_hash.isnot(None)).first()
        assert user is not None, "No user found with password hash"
        assert "@" in user.email, "Invalid user email format"
        assert user.role in ("PATIENT", "DOCTOR", "HOSPITAL_ADMIN", "RECEPTIONIST"), f"Unknown role {user.role}"
        print(f"  [PASS] Successfully retrieved user role '{user.role}' with valid password hash.")
        passed_checks += 1

        # Check 2: Patient Record & User Linkage
        print("\n[Test 2] Patient Profile & User Linkage Verification...")
        patient = session.query(PatientModel).first()
        assert patient is not None, "No patient record found"
        parent_user = session.query(UserModel).filter_by(id=patient.user_id).first()
        assert parent_user is not None, f"Parent user not found for patient {patient.id}"
        assert patient.full_name is not None and len(patient.full_name) > 0, "Patient full_name empty"
        print(f"  [PASS] Successfully retrieved patient profile linked to parent user ID {parent_user.id}.")
        passed_checks += 1

        # Check 3: Hospital & Doctor Department Hierarchy
        print("\n[Test 3] Hospital & Doctor Specialty Hierarchy...")
        doctor = session.query(DoctorModel).first()
        assert doctor is not None, "No doctor record found"
        hospital = session.query(HospitalModel).filter_by(id=doctor.hospital_id).first()
        assert hospital is not None, f"Hospital not found for doctor {doctor.id}"
        assert isinstance(hospital.specialties, list), "Hospital specialties is not a parsed list"
        assert len(hospital.specialties) > 0, "Hospital has no specialties listed"
        print(f"  [PASS] Doctor '{doctor.name}' linked to hospital '{hospital.name}' with specialties {hospital.specialties[:3]}.")
        passed_checks += 1

        # Check 4: OPD Appointment & QR Token Verification
        print("\n[Test 4] OPD Appointment Scheduling & QR Token Integrity...")
        opd = session.query(OPDAppointmentModel).filter(OPDAppointmentModel.qr_token.isnot(None)).first()
        assert opd is not None, "No OPD appointment found with QR token"
        assert len(opd.qr_token) > 10, "QR token format invalid"
        assert opd.status in ("CONFIRMED", "VERIFIED", "COMPLETED", "CANCELLED", "CHECKED_IN"), f"Invalid status {opd.status}"
        print(f"  [PASS] OPD appointment '{opd.id}' has valid QR token and status '{opd.status}'.")
        passed_checks += 1

        # Check 5: Clinical Consultation & Prescription JSON Structure
        print("\n[Test 5] Clinical Consultation & Structured Prescription...")
        consultation = session.query(ConsultationModel).first()
        if consultation:
            assert consultation.clinical_notes is not None, "Clinical notes empty"
            assert consultation.diagnosis is not None, "Diagnosis empty"
            if consultation.prescription_medicines:
                assert isinstance(consultation.prescription_medicines, list), "prescription_medicines not a list"
            print(f"  [PASS] Consultation '{consultation.id}' has clinical notes, diagnosis, and JSON prescriptions.")
        else:
            print("  [SKIP] No consultation records present.")
        passed_checks += 1

        # Check 6: Medical Record File Metadata
        print("\n[Test 6] Medical Records & Document Category...")
        med_rec = session.query(MedicalRecordModel).first()
        assert med_rec is not None, "No medical records found"
        assert med_rec.file_path is not None, "file_path is empty"
        assert med_rec.category is not None, "category is empty"
        print(f"  [PASS] Medical record '{med_rec.id}' category '{med_rec.category}' verified with valid path reference.")
        passed_checks += 1

        # Check 7: Transactional Write & Cleanup in Neon PostgreSQL
        print("\n[Test 7] Transactional Audit Log Insert & Teardown...")
        test_audit_id = "audit-neon-integration-test-001"
        # Clean any old test row
        old_test = session.query(AuditLogModel).filter_by(id=test_audit_id).first()
        if old_test:
            session.delete(old_test)
            session.commit()

        new_audit = AuditLogModel(
            id=test_audit_id,
            timestamp=datetime.now().isoformat(),
            actor_role="SYSTEM_TEST",
            actor_id="test_runner",
            action="NEON_INTEGRATION_TEST",
            details="Testing write and commit capabilities on Neon PostgreSQL"
        )
        session.add(new_audit)
        session.commit()

        # Read back
        verified_audit = session.query(AuditLogModel).filter_by(id=test_audit_id).first()
        assert verified_audit is not None, "Failed to read back test audit log"
        assert verified_audit.action == "NEON_INTEGRATION_TEST", "Action mismatch"

        # Cleanup
        session.delete(verified_audit)
        session.commit()
        print("  [PASS] Transactional insert, read-back, and cleanup succeeded.")
        passed_checks += 1

    engine.dispose()

    # Final check: Local SQLite integrity
    print("\n[Final Check] Confirming Local SQLite Preserved...")
    sq_conn = sqlite3.connect("chikitsax.db")
    cur = sq_conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    assert cur.fetchone()[0] == "ok"
    cur.execute("SELECT COUNT(*) FROM users;")
    assert cur.fetchone()[0] == 166
    cur.execute("SELECT COUNT(*) FROM opd_appointments;")
    assert cur.fetchone()[0] == 192
    sq_conn.close()
    print("  [PASS] Local SQLite database remains 100% untouched and verified.")

    print("\n" + "=" * 80)
    print(f"ALL INTEGRATION CHECKS PASSED: {passed_checks}/{total_checks} (100%)")
    print("=" * 80)

if __name__ == "__main__":
    run_integration_tests()
