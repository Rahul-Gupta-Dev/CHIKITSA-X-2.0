# CHIKITSA-X 2.0 — FastAPI Backend Service

Production-ready backend API foundation for Patient Intelligence, Care Navigation & Care-to-Cost Financial Assistance.

---

## 🏗️ Architecture Stack
- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLite (`chikitsax.db` for local dev) / PostgreSQL (production ready) via SQLAlchemy 2.0 ORM
- **Security**: JWT Bearer Authentication, PBKDF2-HMAC-SHA256 password hashing, SlowAPI rate limiting
- **Validation**: Pydantic v2
- **Server**: Uvicorn (ASGI)
- **CORS**: Configurable domain whitelist (default `http://localhost:5173`)

---

## 📁 Directory Structure
```
backend/
├── app/
│   ├── main.py                # FastAPI Application Entrypoint & Middleware
│   ├── database.py            # SQLAlchemy Engine, Sessions & Schema Migrations
│   ├── auth.py                # JWT & PBKDF2 Password Security
│   ├── limiter.py             # Rate Limiting Configuration
│   ├── seed.py                # Stable Demo Dataset Seeder
│   ├── models/                # SQLAlchemy Models (21 relational entities)
│   ├── schemas/               # Pydantic Schemas
│   ├── routers/               # Authenticated REST API Endpoints
│   └── services/              # Modular Services (OCR, Voice, Triage, Care Score, Financial)
├── alembic/                   # Alembic database migrations
├── requirements.txt           # Python Dependencies
├── .env.example               # Environment Variables Template
└── README.md                  # Backend Documentation
```

---

## ⚡ Quickstart Guide

### 1. Python & Virtual Environment
Requires Python 3.10 or higher.

```bash
cd backend
python -m venv venv
```

Activate virtual environment:
- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
- **Linux / macOS**: `source venv/bin/activate`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server automatically initializes database tables in `backend/chikitsax.db` and seeds stable demo dataset on first startup.

---

## 📡 API Endpoints Summary

### Health Check
- `GET /api/health` -> `{"status": "ok", "service": "CHIKITSAX backend"}`

### Authentication
- `POST /api/auth/register` (Public patient registration)
- `POST /api/auth/login` (Role-verified authentication)
- `GET /api/auth/me` (Token session verification)

### Patient & Records
- `GET /api/patients/{patient_id}`
- `POST /api/patients`
- `PUT /api/patients/{patient_id}`
- `GET /api/patients/{patient_id}/profile` (Unified Health Profile with consent verification)
- `GET /api/medical-records/patient/{patient_id}`
- `POST /api/medical-records/upload` (Multipart file upload with OCR text extraction)
- `GET /api/medical-records/{record_id}/download` (Authenticated secure file download)

### Voice Intake & Triage
- `POST /api/intake` (Symptom recording and NLP entity extraction)
- `POST /api/triage` (Rule-based clinical risk triage + medical disclaimer)
- `GET /api/triage/{patient_id}` (Historical triage results)

### Hospitals & Doctors
- `GET /api/hospitals`
- `GET /api/hospitals/{hospital_id}`
- `POST /api/hospitals/{hospital_id}/reviews` (Patient review submission)
- `GET /api/hospitals/{hospital_id}/reviews` (Public verified reviews)
- `POST /api/hospitals/recommend` (Care Score calculation)
- `GET /api/doctors/{doctor_id}`
- `GET /api/doctors/{doctor_id}/appointments` (Doctor-scoped queue)
- `GET /api/doctors/{doctor_id}/schedule` (Blocked and active OPD slots)
- `POST /api/doctors/{doctor_id}/schedule/block-slot` (Schedule management)
- `POST /api/doctors/{doctor_id}/schedule/unblock-slot` (Slot restoration)

### OPD Appointment & Reception Verification
- `POST /api/opd` (Appointment booking with collision lock)
- `GET /api/opd` (Role-scoped appointment listing)
- `PUT /api/opd/{appointment_id}/reschedule`
- `PUT /api/opd/{appointment_id}/cancel`
- `POST /api/qr` (Tokenized pass generation)
- `GET /api/qr/verify/{reference_id}`
- `POST /api/hospital/verify` (Staff-only reception check-in)

### Consent & Doctor Consultations
- `POST /api/consent` (Patient-controlled consent grant)
- `PUT /api/consent/{consent_id}/revoke` (Immediate consent revocation)
- `GET /api/consent/{patient_id}` (Consent history)
- `POST /api/consultations/draft` (Doctor consultation draft persistence)
- `GET /api/consultations/draft/{appointment_id}` (Doctor draft retrieval)
- `POST /api/consultations` (Finalized digital consultation signing)
- `GET /api/consultations/{appointment_id}`

### Care-to-Cost Financial Assistance
- `GET /api/financial/insurance/{patient_id}`
- `GET /api/financial/schemes/{patient_id}`
- `GET /api/financial/ngo-support/{patient_id}`
- `POST /api/financial/assess` (Calculates Insurance, Gov Schemes, NGO grants, Patient Gap)
- `POST /api/financial/finance-plan` (Authenticated scenario calculation)

### Audit Logging
- `GET /api/audit-logs` (Administrative audit retrieval)
- `POST /api/audit-logs` (Tamper-evident event recording)

---

## 🔒 Interactive API Documentation
Once running, open:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
