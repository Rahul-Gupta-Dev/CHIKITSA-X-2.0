import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.database import engine, Base, SessionLocal, apply_safe_migrations
from app.limiter import limiter
from app.seed import seed_database
from app.routers import (
    health_router,
    auth_router,
    patients_router,
    intake_router,
    medical_records_router,
    triage_router,
    hospitals_router,
    opd_router,
    qr_router,
    doctors_router,
    consultations_router,
    consent_router,
    financial_router,
    audit_router,
)

# Initialize database tables
Base.metadata.create_all(bind=engine)
apply_safe_migrations()

# Seed demo dataset
with SessionLocal() as db_session:
    seed_database(db_session)

app = FastAPI(
    title="CHIKITSAX AI-Powered Smart Healthcare API",
    description="Backend API foundation for Patient Intelligence, Care Navigation & Care-to-Cost Financial Assistance",
    version="1.0.0"
)

# Attach Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Fail-safe CORS resolution
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

def resolve_cors_origins() -> list:
    env = os.getenv("ENVIRONMENT", "development").lower()
    cors_origins_str = os.getenv("CORS_ORIGINS", "").strip()
    if not cors_origins_str:
        if env in ["production", "staging"]:
            raise RuntimeError(
                f"CRITICAL PRODUCTION SECURITY ERROR: CORS_ORIGINS must be explicitly configured in '{env}' environment."
            )
        return ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    parsed = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
    if "*" in parsed and env in ["production", "staging"]:
        raise RuntimeError(
            f"CRITICAL PRODUCTION SECURITY ERROR: Wildcard origin '*' with credentials enabled is prohibited in '{env}'."
        )
    return parsed

origins = resolve_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(intake_router)
app.include_router(medical_records_router)
app.include_router(triage_router)
app.include_router(hospitals_router)
app.include_router(opd_router)
app.include_router(qr_router)
app.include_router(doctors_router)
app.include_router(consultations_router)
app.include_router(consent_router)
app.include_router(financial_router)
app.include_router(audit_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to CHIKITSAX Smart Healthcare API Foundation",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
