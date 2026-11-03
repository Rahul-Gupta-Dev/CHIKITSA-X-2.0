import os
import sys
import sqlite3
import json
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(CURRENT_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import build_engine, normalize_database_url
from sqlalchemy import text, inspect

def mask_url(url: str) -> str:
    if "@" in url:
        prefix = url.split("@")[0]
        suffix = url.split("@")[1]
        schema_part = prefix.split("://")[0] if "://" in prefix else "postgresql"
        return f"{schema_part}://***:***@{suffix}"
    return url

def verify_neon_phase8():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("CHIKITSA-X 2.0: PHASE 8.0 STEP 1 NEON POSTGRESQL VERIFICATION")
    print("=" * 80)
    print(f"Target Database: {mask_url(raw_url)}")

    engine = build_engine(normalize_database_url(raw_url))

    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()

        # 1. Verify Alembic Version
        alembic_rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        print(f"\n[1] Alembic Migration Version: {alembic_rev}")
        assert alembic_rev == "f134f7f7b897", f"Expected revision f134f7f7b897, got {alembic_rev}"
        print("    [PASS] Neon PostgreSQL is stamped at revision f134f7f7b897 (HEAD)")

        # 2. Table Count Check
        print(f"\n[2] Database Tables Count: {len(tables)} tables")
        required_new_tables = ["refresh_tokens", "password_reset_tokens", "hospital_invitations", "auth_audit_logs"]
        for nt in required_new_tables:
            assert nt in tables, f"New table '{nt}' missing from Neon PostgreSQL!"
            print(f"    • Detected new auth table: {nt:25} [OK]")

        # 3. Users Table Columns and Preservation
        print("\n[3] Users Table & Identity Verification:")
        user_cols = [c["name"] for c in inspector.get_columns("users")]
        required_user_cols = ["public_id", "account_status", "email_verified", "phone_verified", "approval_status"]
        for uc in required_user_cols:
            assert uc in user_cols, f"Column '{uc}' missing from users table!"
        print(f"    • All new identity columns verified on users: {required_user_cols}")

        total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"    • Total Users: {total_users} (Expected: 167)")
        assert total_users == 167, f"User count mismatch: {total_users} != 167"

        null_public_ids = conn.execute(text("SELECT COUNT(*) FROM users WHERE public_id IS NULL")).scalar()
        print(f"    • Users with NULL public_id: {null_public_ids}")
        assert null_public_ids == 0, "Some users have NULL public_id!"

        unique_public_ids = conn.execute(text("SELECT COUNT(DISTINCT public_id) FROM users")).scalar()
        print(f"    • Distinct public_ids: {unique_public_ids}")
        assert unique_public_ids == 167, "Duplicate public_id detected!"

        # Demo users check
        demo_p = conn.execute(text("SELECT id, public_id, account_status, approval_status FROM users WHERE id = 'usr-patient-1'")).fetchone()
        demo_d = conn.execute(text("SELECT id, public_id, account_status, approval_status FROM users WHERE id = 'usr-doctor-1'")).fetchone()
        demo_h = conn.execute(text("SELECT id, public_id, account_status, approval_status FROM users WHERE id = 'usr-hospital-1'")).fetchone()
        print(f"    • Patient Demo:  ID={demo_p[0]}, PublicID={demo_p[1]}, Status={demo_p[2]}, Approval={demo_p[3]}")
        print(f"    • Doctor Demo:   ID={demo_d[0]}, PublicID={demo_d[1]}, Status={demo_d[2]}, Approval={demo_d[3]}")
        print(f"    • Hospital Demo: ID={demo_h[0]}, PublicID={demo_h[1]}, Status={demo_h[2]}, Approval={demo_h[3]}")
        assert demo_p[1] == "CHX-P-00000001" and demo_p[2] == "ACTIVE"
        assert demo_d[1] == "CHX-D-00000001" and demo_d[2] == "ACTIVE"
        assert demo_h[1] == "CHX-H-00000001" and demo_h[2] == "ACTIVE"
        print("    [PASS] Core demo identities audited and assigned canonical public IDs.")

        # 4. Doctors Mapping & FK Check
        print("\n[4] Doctors Table & Relationship Verification:")
        doc_cols = [c["name"] for c in inspector.get_columns("doctors")]
        assert "user_id" in doc_cols and "medical_registration_number" in doc_cols
        print("    • Columns user_id and medical_registration_number verified on doctors.")

        doc_fks = inspector.get_foreign_keys("doctors")
        user_fk = [fk for fk in doc_fks if fk["referred_table"] == "users"]
        print(f"    • Foreign keys on doctors table: {len(doc_fks)}")
        assert len(user_fk) > 0, "Foreign key from doctors to users is missing!"
        print(f"    • FK on doctors: {user_fk[0]['constrained_columns']} -> {user_fk[0]['referred_table']}.{user_fk[0]['referred_columns']} [PASS]")

        doc1 = conn.execute(text("SELECT id, name, user_id, medical_registration_number, verification_status FROM doctors WHERE id = 'doc-1'")).fetchone()
        doc2 = conn.execute(text("SELECT id, name, user_id, medical_registration_number, verification_status FROM doctors WHERE id = 'doc-2'")).fetchone()
        print(f"    • doc-1: {doc1[1]} -> user_id={doc1[2]}, RegNo={doc1[3]}, Status={doc1[4]}")
        print(f"    • doc-2: {doc2[1]} -> user_id={doc2[2]}, RegNo={doc2[3]}, Status={doc2[4]}")
        assert doc1[2] == "usr-doctor-1", "doc-1 not linked to usr-doctor-1"
        assert doc2[2] is None, "doc-2 should remain unlinked (user_id=None) pending manual verification"
        print("    [PASS] Doctor mappings verified according to strict specification.")

        # 5. Row Counts & Data Preservation across all tables
        print("\n[5] Table-by-Table Row Count Audit (Before vs After Migration):")
        expected_counts = {
            "users": 167,
            "patients": 145,
            "doctors": 2,
            "hospitals": 3,
            "opd_appointments": 192,
            "qr_references": 192,
            "consultations": 10,
            "consultation_drafts": 0,
            "medical_records": 33,
            "intake_sessions": 16,
            "triage_results": 7,
            "treatment_cost_estimates": 37,
            "care_to_cost_assessments": 8,
            "insurance_policies": 1,
            "insurance_claims": 0,
            "government_schemes": 2,
            "ngo_support": 2,
            "consent_logs": 34,
            "hospital_reviews": 0,
            "audit_logs": 11,
            "refresh_tokens": 0,
            "password_reset_tokens": 0,
            "hospital_invitations": 0,
            "auth_audit_logs": 0
        }

        all_counts_match = True
        for tbl, exp_cnt in expected_counts.items():
            actual = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
            status = "MATCH" if actual == exp_cnt else f"MISMATCH ({actual} != {exp_cnt})"
            if actual != exp_cnt:
                all_counts_match = False
            print(f"    • {tbl:<26}: {actual:4} rows [{status}]")
        assert all_counts_match, "Row count mismatch detected after migration!"

        # 6. OPD Appointments & Consultations Integrity
        print("\n[6] OPD & Clinical Consultation Workflow Integrity:")
        sample_opds = conn.execute(text("SELECT id, patient_name, hospital_id, doctor_id, status FROM opd_appointments LIMIT 5")).fetchall()
        for opd in sample_opds:
            assert opd[2] is not None and opd[3] is not None
        print(f"    • Verified sample OPD appointments have valid hospital and doctor IDs.")

        sample_cons = conn.execute(text("SELECT id, appointment_id, patient_name, doctor_name, diagnosis FROM consultations LIMIT 3")).fetchall()
        for c in sample_cons:
            assert c[1] is not None and c[4] is not None
        print(f"    • Verified sample clinical consultations have intact diagnosis and appointment references.")

    engine.dispose()

    # 7. Local SQLite Database Check
    print("\n[7] Confirming Local SQLite Database Preserved:")
    sq_conn = sqlite3.connect("chikitsax.db")
    cur = sq_conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    sq_health = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users;")
    sq_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM opd_appointments;")
    sq_opds = cur.fetchone()[0]
    sq_conn.close()

    print(f"    • SQLite Integrity: {sq_health}")
    print(f"    • SQLite Users:     {sq_users} (Unchanged)")
    print(f"    • SQLite OPDs:      {sq_opds} (Unchanged)")
    assert sq_health == "ok" and sq_users == 167 and sq_opds == 192
    print("    [PASS] Local SQLite database completely intact and untouched.")

    print("\n" + "=" * 80)
    print("ALL PHASE 8.0 STEP 1 VERIFICATION CHECKS PASSED (100% SUCCESS)")
    print("=" * 80)

if __name__ == "__main__":
    verify_neon_phase8()
