import os
import sys
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(CURRENT_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import normalize_database_url, build_engine
from sqlalchemy import text

def mask_url(url: str) -> str:
    if "@" in url:
        prefix = url.split("@")[0]
        suffix = url.split("@")[1]
        schema_part = prefix.split("://")[0] if "://" in prefix else "postgresql"
        return f"{schema_part}://***:***@{suffix}"
    return url

def test_connection():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("NEON MANAGED POSTGRESQL CONNECTIVITY & HEALTH CHECK")
    print("=" * 80)
    print(f"Target URL: {mask_url(raw_url)}")

    norm_url = normalize_database_url(raw_url)
    engine = build_engine(norm_url)

    try:
        with engine.connect() as conn:
            # 1. SELECT 1
            res_one = conn.execute(text("SELECT 1;")).scalar()
            assert res_one == 1, f"Expected 1, got {res_one}"
            print("[PASS] Query 1: SELECT 1 -> 1 (Connection Active)")

            # 2. current_database()
            curr_db = conn.execute(text("SELECT current_database();")).scalar()
            print(f"[PASS] Query 2: current_database() -> {curr_db}")

            # 3. current_user
            curr_user = conn.execute(text("SELECT current_user;")).scalar()
            print(f"[PASS] Query 3: current_user -> {curr_user}")

            # 4. version()
            pg_ver = conn.execute(text("SELECT version();")).scalar()
            print(f"[PASS] Query 4: version() -> {pg_ver}")

            # 5. Dialect & Driver info
            print(f"[PASS] SQLAlchemy Dialect: {engine.dialect.name} ({engine.driver})")

            # 6. Check existing tables in public schema
            tables_query = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)).fetchall()
            table_names = [t[0] for t in tables_query]
            print(f"[INFO] Existing Public Tables Count: {len(table_names)}")
            if table_names:
                print(f"[INFO] Detected Tables: {', '.join(table_names)}")
            else:
                print("[INFO] Database is currently fresh/empty (0 tables in public schema).")

    except Exception as e:
        print(f"[FAIL] PostgreSQL Connection Failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        engine.dispose()

    print("=" * 80)
    print("ALL CONNECTIVITY CHECKS COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    test_connection()
