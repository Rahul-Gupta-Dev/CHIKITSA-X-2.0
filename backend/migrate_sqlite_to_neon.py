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

from app.database import Base, build_engine, normalize_database_url, apply_safe_migrations
import app.models
from sqlalchemy import inspect, text, JSON, DateTime, Date, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import insert as pg_insert

def mask_url(url: str) -> str:
    if "@" in url:
        prefix = url.split("@")[0]
        suffix = url.split("@")[1]
        schema_part = prefix.split("://")[0] if "://" in prefix else "postgresql"
        return f"{schema_part}://***:***@{suffix}"
    return url

# Strict dependency order respecting foreign keys
TABLE_MIGRATION_ORDER = [
    "hospitals",
    "users",
    "doctors",
    "patients",
    "opd_appointments",
    "qr_references",
    "consultations",
    "consultation_drafts",
    "medical_records",
    "intake_sessions",
    "triage_results",
    "treatment_cost_estimates",
    "care_to_cost_assessments",
    "insurance_policies",
    "insurance_claims",
    "government_schemes",
    "ngo_support",
    "consent_logs",
    "hospital_reviews",
    "audit_logs"
]

def parse_val(col_name, val, col_type):
    if val is None:
        return None
    if isinstance(col_type, JSON):
        if isinstance(val, str):
            val_strip = val.strip()
            if (val_strip.startswith("{") and val_strip.endswith("}")) or (val_strip.startswith("[") and val_strip.endswith("]")):
                try:
                    return json.loads(val_strip)
                except Exception:
                    return val
            if val_strip in ("", "null"):
                return None
        return val
    elif isinstance(col_type, DateTime):
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            v = val.strip()
            if not v:
                return None
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(v, fmt)
                    except ValueError:
                        pass
        return val
    elif isinstance(col_type, Boolean):
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.strip().lower() in ("true", "1", "t", "yes")
        return bool(val)
    elif isinstance(col_type, Integer):
        if isinstance(val, str) and val.strip().isdigit():
            return int(val.strip())
        return val
    elif isinstance(col_type, Float):
        if isinstance(val, (int, str)):
            try:
                return float(val)
            except ValueError:
                return val
        return val
    return val

def run_migration():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL is not configured in backend/.env", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("CHIKITSA-X 2.0: FULL SQLITE TO NEON MANAGED POSTGRESQL DATA MIGRATION")
    print("=" * 80)
    print(f"Target: {mask_url(raw_url)}")
    
    sqlite_db_path = os.path.join(CURRENT_DIR, "chikitsax.db")
    if not os.path.exists(sqlite_db_path):
        print(f"[ERROR] SQLite database not found at {sqlite_db_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Connect SQLite (Read-Only)
    sqlite_conn = sqlite3.connect(f"file:{sqlite_db_path}?mode=ro", uri=True)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # 2. Build PostgreSQL Engine
    norm_url = normalize_database_url(raw_url)
    pg_engine = build_engine(norm_url)

    # Ensure schema is applied
    Base.metadata.create_all(bind=pg_engine)
    apply_safe_migrations(target_engine=pg_engine)

    # Map tables to SQLAlchemy model classes
    models_dict = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}

    migration_stats = {}
    total_migrated_records = 0
    total_skipped_records = 0

    print("\n[Phase 1] Executing Idempotent Batch Migration...")

    with pg_engine.connect() as pg_conn:
        for table_name in TABLE_MIGRATION_ORDER:
            model_cls = models_dict.get(table_name)
            if not model_cls:
                print(f"[WARN] No SQLAlchemy model registered for table '{table_name}'. Skipping.")
                continue

            table_obj = model_cls.__table__
            col_types = {c.name: c.type for c in table_obj.columns}
            pk_cols = [c.name for c in table_obj.primary_key.columns]

            # Read rows from SQLite
            sqlite_cur.execute(f"SELECT * FROM {table_name}")
            sqlite_rows = sqlite_cur.fetchall()
            src_count = len(sqlite_rows)

            if src_count == 0:
                print(f"  • {table_name:28}: 0 records to migrate (empty table).")
                migration_stats[table_name] = {
                    "source_count": 0,
                    "target_count_before": 0,
                    "migrated": 0,
                    "target_count_after": 0,
                    "status": "EMPTY"
                }
                continue

            # Transform rows
            transformed_rows = []
            for r in sqlite_rows:
                d = dict(r)
                row_dict = {}
                for col_name, val in d.items():
                    c_type = col_types.get(col_name)
                    row_dict[col_name] = parse_val(col_name, val, c_type)
                transformed_rows.append(row_dict)

            # Query count in Neon before insert
            count_before = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()

            # Batch insert in chunks of 100 with on_conflict_do_nothing
            chunk_size = 100
            for i in range(0, len(transformed_rows), chunk_size):
                chunk = transformed_rows[i:i + chunk_size]
                stmt = pg_insert(table_obj).values(chunk)
                if pk_cols:
                    stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
                pg_conn.execute(stmt)
            pg_conn.commit()

            # Query count in Neon after insert
            count_after = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
            newly_inserted = count_after - count_before

            total_migrated_records += newly_inserted
            status = "MATCH" if count_after == src_count else ("PARTIAL" if count_after < src_count else "EXCEEDS")
            
            migration_stats[table_name] = {
                "source_count": src_count,
                "target_count_before": count_before,
                "inserted": newly_inserted,
                "target_count_after": count_after,
                "status": status
            }

            print(f"  • {table_name:28}: Source={src_count:4} | Inserted={newly_inserted:4} | Total Neon={count_after:4} [{status}]")

    sqlite_conn.close()
    pg_engine.dispose()

    print("\n" + "=" * 80)
    print("MIGRATION EXECUTION COMPLETE")
    print(f"Total rows inserted in this run: {total_migrated_records}")
    print("=" * 80)

    # Save migration summary
    summary_path = os.path.join(CURRENT_DIR, "migration_stats.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(migration_stats, fh, indent=2)

    return migration_stats

if __name__ == "__main__":
    run_migration()
