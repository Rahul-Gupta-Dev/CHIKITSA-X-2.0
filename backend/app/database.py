import os
import threading
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import create_engine, text, inspect, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Global lock to serialize slot bookings, cancellations, rescheduling, and doctor schedule blocking
SLOT_MUTATION_LOCK = threading.RLock()

# Connection-level SQLite foreign-key enforcement
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

DEFAULT_DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chikitsax.db")

def normalize_database_url(url: str) -> str:
    """Normalize legacy and cloud URL formats to secure SQLAlchemy dialects."""
    if not url or url.strip() in ["sqlite:///./chikitsax.db", "sqlite:///chikitsax.db"]:
        return f"sqlite:///{DEFAULT_DB_FILE.replace(os.sep, '/')}"
    clean = url.strip()
    if clean.startswith("postgres://"):
        return clean.replace("postgres://", "postgresql+psycopg2://", 1)
    elif clean.startswith("postgresql://") and "+psycopg2" not in clean and "+asyncpg" not in clean:
        return clean.replace("postgresql://", "postgresql+psycopg2://", 1)
    return clean

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", ""))

def build_engine(db_url: str):
    """Build a SQLAlchemy engine with environment-appropriate pooling and connection arguments."""
    is_sqlite = db_url.startswith("sqlite")
    kwargs = {}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL Production / Staging Pooling Settings
        kwargs["pool_pre_ping"] = True
        kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
        kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "1800"))
        kwargs["pool_timeout"] = int(os.getenv("DB_POOL_TIMEOUT", "30"))

        ssl_mode = os.getenv("DB_SSLMODE")
        if ssl_mode:
            kwargs["connect_args"] = {"sslmode": ssl_mode}

    return create_engine(db_url, **kwargs)

engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def apply_safe_migrations(target_engine=None):
    """Safely apply non-destructive schema migrations and unique constraints without dropping data."""
    eng = target_engine or engine
    try:
        inspector = inspect(eng)
        existing_tables = inspector.get_table_names()

        with eng.begin() as conn:
            if "users" in existing_tables:
                columns = [c["name"] for c in inspector.get_columns("users")]
                if "password_hash" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))

            if "medical_records" in existing_tables:
                columns = [c["name"] for c in inspector.get_columns("medical_records")]
                if "file_path" not in columns:
                    conn.execute(text("ALTER TABLE medical_records ADD COLUMN file_path VARCHAR"))

            if "doctors" in existing_tables:
                columns = [c["name"] for c in inspector.get_columns("doctors")]
                if "weekly_schedule" not in columns:
                    conn.execute(text("ALTER TABLE doctors ADD COLUMN weekly_schedule JSON"))
                if "blocked_slots" not in columns:
                    conn.execute(text("ALTER TABLE doctors ADD COLUMN blocked_slots JSON"))

            if "opd_appointments" in existing_tables:
                columns = [c["name"] for c in inspector.get_columns("opd_appointments")]
                if "active_slot_lock" not in columns:
                    conn.execute(text("ALTER TABLE opd_appointments ADD COLUMN active_slot_lock VARCHAR"))
                # Ensure unique index exists
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_active_slot_lock ON opd_appointments (active_slot_lock)"))

            if "consultations" in existing_tables:
                # Ensure unique index exists on appointment_id
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_consultation_appointment_id ON consultations (appointment_id)"))

        # Ensure all tables are created safely
        Base.metadata.create_all(bind=eng)
    except Exception as e:
        print(f"Migration notice: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
