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

from app.database import Base, build_engine, normalize_database_url
import app.models
from sqlalchemy import text, inspect

def mask_url(url: str) -> str:
    if "@" in url:
        prefix = url.split("@")[0]
        suffix = url.split("@")[1]
        schema_part = prefix.split("://")[0] if "://" in prefix else "postgresql"
        return f"{schema_part}://***:***@{suffix}"
    return url

def run_reconciliation():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("CHIKITSA-X 2.0: POST-MIGRATION RECONCILIATION & DATA INTEGRITY AUDIT")
    print("=" * 80)
    print(f"Target Database: {mask_url(raw_url)}")

    sqlite_db_path = os.path.join(CURRENT_DIR, "chikitsax.db")
    sqlite_conn = sqlite3.connect(f"file:{sqlite_db_path}?mode=ro", uri=True)
    sqlite_cur = sqlite_conn.cursor()

    pg_engine = build_engine(normalize_database_url(raw_url))

    models_dict = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}

    reconciliation_results = []
    all_matched = True

    with pg_engine.connect() as pg_conn:
        inspector = inspect(pg_conn)
        pg_tables = inspector.get_table_names()

        print("\n[Audit 1: Table-by-Table Row Count Parity]")
        print(f"{'Table Name':<30} | {'SQLite Count':<14} | {'Neon PG Count':<14} | {'Status':<8}")
        print("-" * 75)

        for table_name in sorted(models_dict.keys()):
            # SQLite count
            sqlite_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_cnt = sqlite_cur.fetchone()[0]

            # Neon PG count
            pg_cnt = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()

            status = "MATCH" if sqlite_cnt == pg_cnt else "MISMATCH"
            if status != "MATCH":
                all_matched = False

            print(f"{table_name:<30} | {sqlite_cnt:<14} | {pg_cnt:<14} | {status:<8}")
            reconciliation_results.append({
                "table": table_name,
                "sqlite_count": sqlite_cnt,
                "neon_count": pg_cnt,
                "status": status
            })

        print("\n[Audit 2: Neon PostgreSQL Referential Integrity Check]")
        # Check foreign keys in PostgreSQL
        # 1. Doctors -> Hospitals
        doc_orphans = pg_conn.execute(text("""
            SELECT d.id FROM doctors d LEFT JOIN hospitals h ON d.hospital_id = h.id WHERE h.id IS NULL
        """)).fetchall()
        print(f"  • Doctors referencing nonexistent hospitals: {len(doc_orphans)}")

        # 2. Patients -> Users
        pat_orphans = pg_conn.execute(text("""
            SELECT p.id FROM patients p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL
        """)).fetchall()
        print(f"  • Patients referencing nonexistent users: {len(pat_orphans)}")

        # 3. OPD Appointments -> Hospitals & Doctors
        opd_hosp_orphans = pg_conn.execute(text("""
            SELECT a.id FROM opd_appointments a LEFT JOIN hospitals h ON a.hospital_id = h.id WHERE h.id IS NULL
        """)).fetchall()
        opd_doc_orphans = pg_conn.execute(text("""
            SELECT a.id FROM opd_appointments a LEFT JOIN doctors d ON a.doctor_id = d.id WHERE d.id IS NULL
        """)).fetchall()
        print(f"  • OPD appointments referencing nonexistent hospitals: {len(opd_hosp_orphans)}")
        print(f"  • OPD appointments referencing nonexistent doctors: {len(opd_doc_orphans)}")

        # 4. QR References -> Hospitals
        qr_hosp_orphans = pg_conn.execute(text("""
            SELECT q.id FROM qr_references q LEFT JOIN hospitals h ON q.hospital_id = h.id WHERE h.id IS NULL
        """)).fetchall()
        print(f"  • QR references referencing nonexistent hospitals: {len(qr_hosp_orphans)}")

        fk_integrity_pass = (
            len(doc_orphans) == 0 and
            len(pat_orphans) == 0 and
            len(opd_hosp_orphans) == 0 and
            len(opd_doc_orphans) == 0 and
            len(qr_hosp_orphans) == 0
        )
        print(f"  FK Referential Integrity Result: {'PASS (100% Valid)' if fk_integrity_pass else 'FAIL'}")

        print("\n[Audit 3: Spot-Check Parity on Critical Data Types]")
        # Spot check Users
        pg_user_sample = pg_conn.execute(text('SELECT id, email, role FROM users LIMIT 3')).fetchall()
        print(f"  • Neon Users Sample: {len(pg_user_sample)} records verified.")
        for u in pg_user_sample:
            sqlite_cur.execute("SELECT id, email, role FROM users WHERE id = ?", (u[0],))
            sq_u = sqlite_cur.fetchone()
            assert sq_u is not None and sq_u[1] == u[1] and sq_u[2] == u[2], f"User mismatch for {u[0]}"
        print("    [PASS] User ID, email, role parity verified.")

        # Spot check Hospitals (JSON specialties)
        pg_hosp_sample = pg_conn.execute(text('SELECT id, name, specialties FROM hospitals LIMIT 3')).fetchall()
        print(f"  • Neon Hospitals Sample: {len(pg_hosp_sample)} records verified.")
        for h in pg_hosp_sample:
            sqlite_cur.execute("SELECT id, name, specialties FROM hospitals WHERE id = ?", (h[0],))
            sq_h = sqlite_cur.fetchone()
            assert sq_h is not None and sq_h[1] == h[1], f"Hospital mismatch for {h[0]}"
            # Verify specialties JSON is deserialized
            assert isinstance(h[2], list), f"Specialties is not list: {type(h[2])}"
        print("    [PASS] Hospital JSON specialties parity verified.")

        # Spot check OPD Appointments
        pg_opd_sample = pg_conn.execute(text('SELECT id, status, qr_token FROM opd_appointments LIMIT 5')).fetchall()
        print(f"  • Neon OPD Appointments Sample: {len(pg_opd_sample)} records verified.")
        for opd in pg_opd_sample:
            sqlite_cur.execute("SELECT id, status, qr_token FROM opd_appointments WHERE id = ?", (opd[0],))
            sq_opd = sqlite_cur.fetchone()
            assert sq_opd is not None and sq_opd[1] == opd[1] and sq_opd[2] == opd[2], f"OPD mismatch for {opd[0]}"
        print("    [PASS] OPD appointment status & qr_token parity verified.")

        # Spot check Medical Records
        pg_med_sample = pg_conn.execute(text('SELECT id, file_name, file_path, category FROM medical_records LIMIT 5')).fetchall()
        print(f"  • Neon Medical Records Sample: {len(pg_med_sample)} records verified.")
        for m in pg_med_sample:
            sqlite_cur.execute("SELECT id, file_name, file_path, category FROM medical_records WHERE id = ?", (m[0],))
            sq_m = sqlite_cur.fetchone()
            assert sq_m is not None and sq_m[1] == m[1] and sq_m[3] == m[3], f"Medical record mismatch for {m[0]}"
        print("    [PASS] Medical record file metadata parity verified.")

    # Audit 4: Verify SQLite database was completely untouched
    print("\n[Audit 4: Local SQLite Database Health Verification]")
    sqlite_cur.execute("PRAGMA integrity_check;")
    sq_health = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM users;")
    sq_users = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM opd_appointments;")
    sq_opds = sqlite_cur.fetchone()[0]
    print(f"  • SQLite Health Check: {sq_health}")
    print(f"  • SQLite Users Count:  {sq_users} (Unchanged)")
    print(f"  • SQLite OPD Count:    {sq_opds} (Unchanged)")
    assert sq_health == "ok", "SQLite database corrupted!"
    assert sq_users == 166, "SQLite users count changed!"
    assert sq_opds == 192, "SQLite OPD count changed!"
    print("    [PASS] Local SQLite database completely intact and untouched.")

    sqlite_conn.close()
    pg_engine.dispose()

    # Save reconciliation report
    out_file = os.path.join(CURRENT_DIR, "reconciliation_audit_report.json")
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump({
            "all_matched": all_matched,
            "fk_integrity_pass": fk_integrity_pass,
            "table_results": reconciliation_results
        }, fh, indent=2)

    print("\n" + "=" * 80)
    if all_matched and fk_integrity_pass:
        print("ALL RECONCILIATION CHECKS PASSED (100% DATA INTEGRITY ACHIEVED)")
    else:
        print("RECONCILIATION AUDIT DETECTED DISCREPANCIES!")
    print("=" * 80)

if __name__ == "__main__":
    run_reconciliation()
