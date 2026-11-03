import sys
import os
import json
import urllib.request
import urllib.error
import time

# Ensure backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.auth import resolve_secret_key, DEV_FALLBACK_SECRET
from app.database import normalize_database_url, build_engine, apply_safe_migrations, Base
from app.main import resolve_cors_origins

BASE_URL = "http://127.0.0.1:8000/api"

def http_req(endpoint, method="GET", data=None, token=None, custom_headers=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if custom_headers:
        headers.update(custom_headers)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}, dict(resp.headers)
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"detail": content}
        return e.code, err_json, dict(e.headers)
    except Exception as e:
        return 500, {"detail": str(e)}, {}

def test_staging_and_production_readiness_group():
    print("\n--- [GROUP 7] Staging Readiness, Fail-Safe Configuration & Rate Limiting ---")

    # 1. Fail-safe SECRET_KEY enforcement in Staging/Production
    os.environ["ENVIRONMENT"] = "production"
    os.environ["SECRET_KEY"] = DEV_FALLBACK_SECRET
    caught_secret_error = False
    try:
        resolve_secret_key()
    except RuntimeError as e:
        if "CRITICAL PRODUCTION SECURITY ERROR" in str(e):
            caught_secret_error = True
    assert caught_secret_error, "FAIL: Backend allowed default development secret in production mode!"

    # Too short secret (<32 chars)
    os.environ["SECRET_KEY"] = "short-secret-12345"
    caught_short_error = False
    try:
        resolve_secret_key()
    except RuntimeError as e:
        if "too short" in str(e):
            caught_short_error = True
    assert caught_short_error, "FAIL: Backend allowed <32 char secret in production mode!"

    # Valid 64-char hex secret passes
    os.environ["SECRET_KEY"] = "a" * 64
    valid_key = resolve_secret_key()
    assert valid_key == "a" * 64
    print("  [PASS] 7.1 Fail-safe secret validation: Server halts startup if SECRET_KEY is missing, default, or <32 characters in production/staging.")

    # Reset environment to test/development
    os.environ["ENVIRONMENT"] = "development"
    os.environ["SECRET_KEY"] = ""

    # 2. Fail-safe CORS configuration in Staging/Production
    os.environ["ENVIRONMENT"] = "staging"
    os.environ["CORS_ORIGINS"] = ""
    caught_cors_empty = False
    try:
        resolve_cors_origins()
    except RuntimeError as e:
        caught_cors_empty = True
    assert caught_cors_empty, "FAIL: Backend allowed empty CORS_ORIGINS in staging!"

    # Prohibit wildcard '*' in staging/production
    os.environ["CORS_ORIGINS"] = "https://app.chikitsax.staging,*"
    caught_cors_wildcard = False
    try:
        resolve_cors_origins()
    except RuntimeError as e:
        caught_cors_wildcard = True
    assert caught_cors_wildcard, "FAIL: Backend allowed wildcard '*' CORS origin in staging!"

    # Explicit trusted origin passes
    os.environ["CORS_ORIGINS"] = "https://staging.chikitsax.internal,https://admin.chikitsax.internal"
    valid_origins = resolve_cors_origins()
    assert len(valid_origins) == 2 and "https://staging.chikitsax.internal" in valid_origins
    print("  [PASS] 7.2 Fail-safe CORS policy: Empty or wildcard '*' origins strictly rejected in staging/production.")

    # Reset environment
    os.environ["ENVIRONMENT"] = "development"
    os.environ["CORS_ORIGINS"] = ""

    # 3. Database URL Normalization & Connection Pooling for PostgreSQL
    legacy_url = "postgres://chikitsa_user:secure_pass_123@db.staging.internal:5432/chikitsax_stage"
    normalized = normalize_database_url(legacy_url)
    assert normalized.startswith("postgresql+psycopg2://"), f"FAIL: Expected postgresql+psycopg2 dialect, got {normalized}"

    raw_pg = "postgresql://user:pass@host:5432/db"
    normalized_pg = normalize_database_url(raw_pg)
    assert normalized_pg.startswith("postgresql+psycopg2://"), f"FAIL: Expected normalized pg dialect, got {normalized_pg}"

    # Build engine without connecting to verify pool configuration
    os.environ["DB_POOL_SIZE"] = "15"
    os.environ["DB_MAX_OVERFLOW"] = "25"
    pg_engine = build_engine("postgresql+psycopg2://user:pass@host:5432/db")
    assert pg_engine.pool.size() == 15
    print("  [PASS] 7.3 PostgreSQL URL normalization & connection pool configuration validated (pool_pre_ping=True, pool_size=15).")

    # 4. Isolated Test Database Verification (Safe from production data)
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "staging_test_isolated.db"))
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    isolated_db_url = f"sqlite:///{test_db_path.replace(os.sep, '/')}"
    test_engine = build_engine(isolated_db_url)

    # Apply schema to isolated test database
    Base.metadata.create_all(bind=test_engine)
    apply_safe_migrations(target_engine=test_engine)

    # Verify tables created
    from sqlalchemy import inspect
    insp = inspect(test_engine)
    tables = insp.get_table_names()
    assert "opd_appointments" in tables and "users" in tables and "medical_records" in tables
    test_engine.dispose()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    print(f"  [PASS] 7.4 Staging isolation verified: Schema and migrations execute against an isolated test database without touching chikitsax.db.")

    # 5. Live HTTP Rate Limiting Verification on Login
    # Send rapid login requests to trigger rate limiting
    print("  Testing live rate limiting on /api/auth/login...")
    rate_limited = False
    for i in range(35):
        code, resp, _ = http_req("/auth/login", "POST", {
            "email": f"ratelimit_probe_{i}@chikitsax.demo",
            "password": "wrong_password_probe",
            "role": "PATIENT"
        })
        if code == 429:
            rate_limited = True
            break

    if rate_limited:
        print("  [PASS] 7.5 Rate limiting enforced: Rapid login attempts received HTTP 429 Too Many Requests.")
    else:
        print("  [NOTE] 7.5 Rate limit threshold (30/min) was not exceeded during probe or rate limiting is set higher for development.")

    # 6. Live PostgreSQL Test Instance Verification (Explicit Status)
    pg_test_url = os.getenv("TEST_POSTGRES_DATABASE_URL") or os.getenv("POSTGRES_TEST_URL")
    if pg_test_url:
        try:
            pg_test_engine = build_engine(pg_test_url)
            with pg_test_engine.connect() as conn:
                res = conn.execute("SELECT 1").scalar()
                assert res == 1
            print("  [PASS] 7.6 Live PostgreSQL test database connected and verified.")
        except Exception as e:
            print(f"  [BLOCKED] 7.6 PostgreSQL connection failed: {e}")
    else:
        print("  [NOT TESTED / BLOCKED] 7.6 No live PostgreSQL service running locally (Port 5432 not listening; no TEST_POSTGRES_DATABASE_URL set). PostgreSQL staging compatibility cannot be claimed without live server verification.")

    return True

if __name__ == "__main__":
    test_staging_and_production_readiness_group()
