import os
import sys
import sqlite3
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(CURRENT_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import Base, normalize_database_url, build_engine, apply_safe_migrations, DEFAULT_DB_FILE
import app.models # Register all models on Base.metadata
from app.models.hospital import HospitalModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect

def mask_url(url: str) -> str:
    if "@" in url:
        prefix = url.split("@")[0]
        suffix = url.split("@")[1]
        schema_part = prefix.split("://")[0] if "://" in prefix else "postgresql"
        return f"{schema_part}://***:***@{suffix}"
    return url

def run_audit_and_crud_verification():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("CHIKITSA-X 2.0: NEON MANAGED POSTGRESQL SCHEMA AUDIT & CRUD VERIFICATION")
    print("=" * 80)
    print(f"Target URL: {mask_url(raw_url)}")

    # 1. Baseline local SQLite status
    sqlite_conn = sqlite3.connect(DEFAULT_DB_FILE)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    sqlite_tables_before = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT count(*) FROM users;")
    sqlite_users_before = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT count(*) FROM opd_appointments;")
    sqlite_opd_before = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("PRAGMA integrity_check;")
    sqlite_integrity_before = sqlite_cur.fetchone()[0]
    sqlite_conn.close()

    print(f"\n[1] Local SQLite Baseline (chikitsax.db):")
    print(f"    - Tables: {sqlite_tables_before}")
    print(f"    - Users:  {sqlite_users_before}")
    print(f"    - OPDs:   {sqlite_opd_before}")
    print(f"    - Health: {sqlite_integrity_before}")

    # 2. Build PostgreSQL Engine
    norm_url = normalize_database_url(raw_url)
    engine = build_engine(norm_url)

    # 3. Apply Schema Creation and Safe Migrations
    print("\n[2] Applying Schema & Non-Destructive Migrations to Neon PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    apply_safe_migrations(target_engine=engine)

    inspector = inspect(engine)
    pg_tables = inspector.get_table_names()
    print(f"    - Successfully detected {len(pg_tables)} tables in Neon PostgreSQL:")
    for t in sorted(pg_tables):
        cols = len(inspector.get_columns(t))
        fks = len(inspector.get_foreign_keys(t))
        idxs = len(inspector.get_indexes(t))
        print(f"      • {t:30} ({cols} cols, {fks} FKs, {idxs} indexes)")

    # 4. CRUD Lifecycle Test on Neon PostgreSQL
    print("\n[3] Executing Synthetic Record Insert & Read on Neon PostgreSQL...")
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    test_hosp_id = "hosp-neon-test-synthetic-1"
    with Session() as s:
        # Cleanup any old test record if exists
        old = s.query(HospitalModel).filter_by(id=test_hosp_id).first()
        if old:
            s.delete(old)
            s.commit()

        test_hosp = HospitalModel(
            id=test_hosp_id,
            name="Neon Regional Specialty Center",
            code="NRSC-TEST",
            tagline="Cloud-Native Managed Care",
            address="100 Cloud Parkway",
            city="Pune",
            phone="020-99887766",
            emergency_phone="020-99887799",
            estimated_cost_range={"min": 10000, "max": 75000},
            specialties=["Cardiology", "Neurology", "Trauma"]
        )
        s.add(test_hosp)
        s.commit()
        print(f"    [PASS] Inserted synthetic hospital record: '{test_hosp.name}' (ID: {test_hosp.id})")

    # 5. Reconnection & Persistence Verification
    print("\n[4] Reconnecting with Fresh Session to Verify Persistence...")
    engine.dispose() # Drop connection pool completely to guarantee fresh socket
    fresh_engine = build_engine(norm_url)
    FreshSession = sessionmaker(bind=fresh_engine, autoflush=False, autocommit=False)

    with FreshSession() as s:
        fetched = s.query(HospitalModel).filter_by(id=test_hosp_id).first()
        assert fetched is not None, "FAILED: Record was not found after reconnecting!"
        assert fetched.name == "Neon Regional Specialty Center", f"Name mismatch: {fetched.name}"
        assert fetched.code == "NRSC-TEST", f"Code mismatch: {fetched.code}"
        assert fetched.specialties == ["Cardiology", "Neurology", "Trauma"], f"JSON mismatch: {fetched.specialties}"
        print(f"    [PASS] Verified persistent record after reconnection:")
        print(f"           Name: {fetched.name}")
        print(f"           Code: {fetched.code}")
        print(f"           JSON Specialties: {fetched.specialties}")

        # Clean up synthetic test record
        s.delete(fetched)
        s.commit()
        print(f"    [PASS] Cleaned up synthetic test record from Neon PostgreSQL.")

    fresh_engine.dispose()

    # 6. Verify Local SQLite Untouched
    print("\n[5] Verifying Local SQLite Database Preservation...")
    sqlite_conn = sqlite3.connect(DEFAULT_DB_FILE)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    sqlite_tables_after = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT count(*) FROM users;")
    sqlite_users_after = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT count(*) FROM opd_appointments;")
    sqlite_opd_after = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("PRAGMA integrity_check;")
    sqlite_integrity_after = sqlite_cur.fetchone()[0]
    sqlite_conn.close()

    assert sqlite_tables_after == sqlite_tables_before, f"SQLite tables changed! {sqlite_tables_before} -> {sqlite_tables_after}"
    assert sqlite_users_after == sqlite_users_before, f"SQLite users changed! {sqlite_users_before} -> {sqlite_users_after}"
    assert sqlite_opd_after == sqlite_opd_before, f"SQLite OPDs changed! {sqlite_opd_before} -> {sqlite_opd_after}"
    assert sqlite_integrity_after == "ok", f"SQLite integrity not ok: {sqlite_integrity_after}"

    print(f"    [PASS] Local SQLite completely untouched:")
    print(f"           Tables: {sqlite_tables_after} (unchanged)")
    print(f"           Users:  {sqlite_users_after} (unchanged)")
    print(f"           OPDs:   {sqlite_opd_after} (unchanged)")
    print(f"           Health: {sqlite_integrity_after}")

    print("\n" + "=" * 80)
    print("ALL NEON MANAGED POSTGRESQL VERIFICATION CHECKS PASSED (100%)")
    print("=" * 80)

if __name__ == "__main__":
    run_audit_and_crud_verification()
