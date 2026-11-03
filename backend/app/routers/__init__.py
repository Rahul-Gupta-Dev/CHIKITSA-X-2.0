from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.patients import router as patients_router
from app.routers.intake import router as intake_router
from app.routers.medical_records import router as medical_records_router
from app.routers.triage import router as triage_router
from app.routers.hospitals import router as hospitals_router
from app.routers.opd import router as opd_router
from app.routers.qr import router as qr_router
from app.routers.doctors import router as doctors_router
from app.routers.consultations import router as consultations_router
from app.routers.consent import router as consent_router
from app.routers.financial import router as financial_router
from app.routers.audit import router as audit_router

__all__ = [
    "health_router",
    "auth_router",
    "patients_router",
    "intake_router",
    "medical_records_router",
    "triage_router",
    "hospitals_router",
    "opd_router",
    "qr_router",
    "doctors_router",
    "consultations_router",
    "consent_router",
    "financial_router",
    "audit_router",
]
