# CHIKITSA-X 2.0 — Unified Patient Intelligence, Care Navigation & Healthcare Financial Gap Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%7C%20TypeScript%20%7C%20Vite-blue)](https://react.dev/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11+-009688)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Database-SQLAlchemy%202.0%20%7C%20SQLite%20%2F%20PostgreSQL-4479A1)](https://www.sqlalchemy.org/)
[![Status](https://img.shields.io/badge/Audit%20Status-76%2F76%20Checks%20Passed-success)](#10-test-execution-commands)

> **Important Medical Notice & Clinical Disclaimer:**  
> **CHIKITSA-X 2.0 is an assistive clinical navigation and healthcare planning decision-support platform.** The AI Symptom Intake, Automated Triage, and Care Scoring capabilities provide informational guidance and preliminary prioritization only. **They do not constitute a certified medical diagnosis, clinical prognosis, or definitive treatment prescription.** In any medical emergency, patients must contact local emergency services immediately (India: 112 / 108) or report to the nearest 24/7 emergency trauma facility.

---

## 1. Project Overview

Medical care in India and developing healthcare ecosystems faces two critical bottlenecks:
1. **Clinical Care Fragmentation:** Patients struggle to interpret preliminary symptoms, organize unstructured physical paper records, choose appropriate hospital specialties, and navigate outpatient queues.
2. **Catastrophic Out-of-Pocket Expenditure:** Unexpected secondary and tertiary medical procedures drive millions of families into financial distress due to unawareness or complex manual reconciliation of Ayushman Bharat PM-JAY, state government health schemes, private insurance policies, and non-profit hospital aid.

**CHIKITSA-X 2.0** unifies the clinical journey and financial planning into a single, cohesive, multi-user healthcare platform:

$$\text{Voice/Text Intake} \longrightarrow \text{Document OCR} \longrightarrow \text{Automated Triage} \longrightarrow \text{Care Score Matching} \longrightarrow \text{OPD Booking} \longrightarrow \text{QR Reception Verification} \longrightarrow \text{ABDM-Style Consent} \longrightarrow \text{Doctor Consultation} \longrightarrow \text{Itemized Cost Estimation} \longrightarrow \text{Financial Gap Calculation}$$

---

## 2. Key Features

- **Multilingual Voice & Text Intake:** Capture patient symptoms in natural speech via Web Speech API or structured text, extracting primary symptoms, duration, and severity markers.
- **Medical Record OCR & Extraction:** Upload clinical documents (prescriptions, diagnostic lab reports, discharge summaries, imaging) with structured entity extraction and non-hallucinatory parsing.
- **Explainable Hospital Care Scoring:** Objective 5-vector evaluation ranking tertiary and community hospitals:
  $$\text{Care Score} = (0.35 \times \text{Clinical Fit}) + (0.25 \times \text{Affordability}) + (0.15 \times \text{Distance}) + (0.15 \times \text{Slot Availability}) + (0.10 \times \text{Support Services})$$
- **Cryptographically Tokenized QR Pass:** Generate verifiable OPD appointment passes encoding single-use tokens; zero raw medical or demographic data is exposed within the QR payload.
- **Strict Role-Based Reception Check-In:** Dedicated hospital panel check-in workflow restricted to authorized hospital administrative staff, eliminating patient self-verification bypasses.
- **Patient-Controlled Medical Consent Lifecycle:** Patient-centric consent architecture allowing patients to grant, inspect, and immediately revoke medical record and profile access to specific doctors and hospitals.
- **Itemized Treatment Cost Generator:** Standardized procedure, bed/ICU, laboratory, and pharmacy itemized cost projections calculated by attending clinicians.
- **Care-to-Cost Financial Gap Engine:** Dynamic real-time calculation resolving net out-of-pocket patient exposure:
  $$\text{Net Gap} = \text{Estimated Cost} - \text{Insurance} - \text{PM-JAY / State Subsidy} - \text{NGO Support} - \text{Personal Savings}$$
- **Emergency Facility Locator:** Instant-access emergency routing with 24/7 ICU status, bed capacity, direct phone dialer, and geolocated mapping.

---

## 3. Dedicated Panels & Workflows

### 🏥 Patient Dashboard
- **Profile & Health Passport:** View ABHA ID, demographics, blood group, emergency contacts, recorded vital signs, active medications, and documented drug allergies.
- **Intake & Triage History:** Review timeline of symptoms, clinical urgency levels, and recommended specialist disciplines.
- **OPD Appointment Manager:** Book hospital outpatient slots, reschedule bookings, download digital QR passes, and monitor reception check-in status.
- **Digital Health Locker:** Upload prescriptions, diagnostic panels, and lab results with encrypted server storage.
- **Privacy & Consent Center:** Approve or immediately revoke doctor and hospital data-access requests.
- **Financial Navigator:** Live financial gap calculator and multi-hospital scenario cost comparisons.

### 🩺 Doctor Dashboard
- **Outpatient Schedule & Queue:** View confirmed, checked-in, and completed appointments for the authenticated physician.
- **Active Slot Management:** Block and unblock specific consultation slots or manage weekly recurring availability in real time.
- **Patient Clinical Context:** View selected appointment details, authenticated vital signs, and triage assessments protected behind verified patient consent.
- **Electronic Health Records (EHR):** Review unlocked digital records and download authenticated diagnostic files.
- **Consultation Workspace:** Draft and save in-progress clinical notes, prescribe medications with dosage guidelines, record formal diagnoses, and finalize digitally signed consultation records.
- **Treatment Cost Estimator:** Generate itemized procedure projections linked directly to patient financial assistance workflows.

### 🏢 Hospital Administration Panel
- **Reception Desk QR Verification:** Scan or enter patient appointment reference codes with cryptographic token validation and automatic patient queue advancement.
- **Hospital OPD Queue Monitor:** Live synchronization of outpatient flow, checked-in patients, cancellations, and doctor queue assignments.
- **Consent Dispatch:** Request patient clinical records authorization upon arrival.
- **Facility Capacity & Reviews:** Public hospital profile maintenance, bed availability tracking, and verified patient reviews aggregation.

---

## 4. Technology Stack

| Layer | Component | Technology |
| :--- | :--- | :--- |
| **Frontend** | Framework | React 19, TypeScript 5.8 |
| | Tooling & Bundler | Vite 8.2 (ESM, Fast Refresh) |
| | Icons & UI | Lucide React, Custom Responsive CSS Design System |
| | Networking | Axios / Fetch API client with automatic JWT bearer interceptor |
| **Backend** | Framework | FastAPI 0.162, Starlette 1.10 |
| | ASGI Web Server | Uvicorn (HTTP/1.1 & WebSockets) |
| | Security & Auth | PyJWT, PBKDF2-HMAC-SHA256 password hashing, HTTPBearer |
| | Rate Limiting | SlowAPI (client IP & reverse-proxy aware token bucket) |
| **Data Layer** | ORM | SQLAlchemy 2.0 (Declarative Base, Foreign Key Pragma enforcement) |
| | Database Engine | SQLite (Development) / PostgreSQL (Staging & Production ready) |
| | Migrations | Alembic / Non-destructive automated safe schema migrator |

---

## 5. Project Directory Architecture

```text
CHIKITSA-X-2.0/
├── backend/
│   ├── alembic/                 # Database migration revision scripts
│   ├── app/
│   │   ├── models/              # SQLAlchemy database models (21 relational entities)
│   │   ├── routers/             # Authenticated REST API route controllers
│   │   │   ├── auth.py          # Registration, login, JWT session resolution
│   │   │   ├── patients.py      # Patient profile, demographic updates, stage lock
│   │   │   ├── doctors.py       # Doctor queues, appointment scoping, scheduling
│   │   │   ├── opd.py           # OPD booking, slot locking, rescheduling
│   │   │   ├── qr.py            # Token generation, staff-only check-in verification
│   │   │   ├── consent.py       # Patient consent grant, revocation, lifecycle
│   │   │   ├── consultations.py # Draft persistence, finalization, 409 conflict lock
│   │   │   ├── medical_records.py # Authenticated uploads, OCR parsing, file stream
│   │   │   ├── financial.py     # Cost calculations, gap analysis, scheme eligibility
│   │   │   ├── hospitals.py     # Hospital directories, reviews, rating aggregation
│   │   │   └── audit.py         # Administrative audit logging
│   │   ├── services/            # Clinical triage, OCR heuristic, Care Score engines
│   │   ├── auth.py              # Cryptographic utilities & RBAC dependencies
│   │   ├── database.py          # Database connection, foreign keys & migrations
│   │   ├── limiter.py           # Rate limiting configuration
│   │   ├── schemas.py           # Pydantic v2 validation models
│   │   ├── seed.py              # Stable demo seed dataset generator
│   │   └── main.py              # FastAPI application bootstrap & CORS resolution
│   ├── tests/                   # Backend unit tests
│   ├── requirements.txt         # Python dependencies
│   ├── alembic.ini              # Alembic configuration
│   └── .env.example             # Backend environment template
├── src/
│   ├── components/
│   │   ├── common/              # UI components, modals, navbar, disclaimer banner
│   │   ├── patient/             # Patient dashboard views, booking workflow, QR pass
│   │   ├── doctor/              # Doctor queue, consultation workspace, cost modal
│   │   └── hospital/            # Reception check-in, queue management, facility views
│   ├── db/                      # Client-side cache synchronization layer
│   ├── services/                # API client services & authentication handlers
│   ├── types/                   # TypeScript clinical and operational interface definitions
│   ├── App.tsx                  # Application entry point & role navigation
│   └── main.tsx                 # React DOM mount point
├── public/                      # Static assets & icons
├── .env.example                 # Frontend environment template
├── .gitignore                   # Comprehensive git exclusions
├── package.json                 # Node.js dependencies and run scripts
├── tsconfig.json                # TypeScript compiler configuration
└── vite.config.ts               # Vite bundler configuration
```

---

## 6. Frontend Setup Instructions

### Prerequisites
- **Node.js:** v18.0.0 or higher (v20+ recommended)
- **npm:** v9.0.0 or higher

### Installation
```bash
# 1. Navigate to the project root directory
cd CHIKITSA-X-2.0

# 2. Install dependencies
npm install

# 3. Create frontend environment configuration
cp .env.example .env

# 4. Start the frontend development server
npm run dev
```

The application interface will be accessible at `http://localhost:5173`.

### Production Build & Type Checking
```bash
# Verify TypeScript types and generate production bundle
npm run build

# Preview production build locally
npm run preview
```

---

## 7. Backend Setup Instructions

### Prerequisites
- **Python:** v3.10, v3.11, or v3.12
- **pip** and **virtualenv**

### Installation
```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
# Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Create backend environment configuration
cp .env.example .env

# 5. Start the FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API service will start on `http://127.0.0.1:8000`.

---

## 8. Environment Variable Configuration

### Frontend (`.env`)
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Backend (`backend/.env`)
```env
# Operating Environment ('development', 'staging', 'production')
ENVIRONMENT=development

# Database Connection (SQLite default; PostgreSQL connection string for staging/production)
DATABASE_URL=sqlite:///./chikitsax.db

# JWT Secret Key (In staging/production, must be at least 32 characters / 256-bit entropy)
SECRET_KEY=replace-with-a-secure-32-character-secret-key-for-production

# JWT Expiration in Minutes (Default: 1440 = 24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Allowed CORS Origins (comma-separated, wildcards prohibited in production)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# Rate Limiter
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=120/minute
```

---

## 9. Database Setup & Management

### SQLite (Default Local Development)
- On initial launch, `app.main` automatically creates tables via SQLAlchemy metadata and applies safe non-destructive schema migrations.
- The default seed script (`app/seed.py`) populates reference hospitals, verified doctor credentials, sample schemes, and reference patients for immediate local verification.
- **Foreign Key Enforcement:** SQLite foreign keys are explicitly enforced via the `PRAGMA foreign_keys=ON` connection listener in `database.py`.

### PostgreSQL Migration (Staging & Production)
To point the application to PostgreSQL:
1. Provide a standard PostgreSQL URL in `backend/.env`:
   ```env
   DATABASE_URL=postgresql://user:password@hostname:5432/chikitsax
   ```
2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

---

## 10. Test Execution Commands

CHIKITSA-X 2.0 maintains a comprehensive regression test suite with **100% passing verification**:

```bash
# Navigate to backend directory with virtual environment active
cd backend

# 1. Phase 5.1 — Critical Authentication & Authorization Hardening (14 checks)
python test_phase5_1_security_hardening.py

# 2. Phase 5.2 — Real Authentication & Session Restoration Integration (12 checks)
python test_phase5_2_frontend_integration.py

# 3. Phase 5.3 — Multi-User Persistence, OCR Extraction & Review Storage (11 checks)
python test_phase5_3_multi_user_persistence.py

# 4. Phase 5.4 — Database Integrity, Concurrency & Race-Condition Guards (8 checks)
python test_phase5_4_concurrency_integrity.py

# 5. Phase 5.5 — End-to-End Multi-User Scoping & Isolation Audits (9 checks)
python test_phase5_5_e2e_production_readiness.py

# 6. Phase 5.6 — Staging Blocker Remediation & Clinical Fallback Removal (7 checks)
python test_phase5_6_staging_blocker_remediation.py

# 7. Cross-Panel OPD Synchronization — Real-Time Patient/Doctor/Hospital Flow (15 checks)
python test_cross_panel_opd_sync.py
```

---

## 11. API Documentation

Interactive OpenAPI documentation is generated automatically:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema:** `http://127.0.0.1:8000/openapi.json`

---

## 12. Security & Privacy Architecture

- **Zero Clear-Text Passwords:** Passwords hashed with PBKDF2-HMAC-SHA256 utilizing unique 16-byte random salts.
- **Strict Role-Based Access Control (RBAC):** Endpoints enforce strict identity checks (`PATIENT`, `DOCTOR`, `HOSPITAL_ADMIN`, `HOSPITAL_STAFF`). Privilege escalation during registration or login is explicitly rejected with `HTTP 403 Forbidden`.
- **In-Depth IDOR Protection:** Patients cannot inspect or download other patients' records or appointments; doctors cannot inspect records or clinical profiles of patients without active consent.
- **Tokenized QR Verification:** Reception check-in QR codes encode cryptographically random single-use tokens; personal health information (PHI) is never embedded in QR codes.
- **Tamper-Resistant Care Stage:** Patient clinical progression stages (1–12) advance only through verified backend clinical workflow milestones and cannot be arbitrarily modified via API requests.
- **Concurrency Locks:** Multithreaded database transactions prevent double-booking of OPD appointment slots (`HTTP 409 Conflict`) and reject duplicate consultation finalizations.

---

## 13. Current Limitations

- **OCR Adapter Heuristics:** Automated document entity extraction relies on secure heuristic parsing. Optical character extraction from low-resolution mobile photographs requires manual clinical review prior to confirmation.
- **Local Document Storage:** Uploaded medical files are persisted to protected server storage (`backend/uploads/medical_records/`); enterprise production requires S3/Azure Blob object store integration.
- **Single-Host WebSockets:** Real-time cross-panel synchronization uses polling and direct API event triggers; distributed horizontal scaling will require Redis pub/sub channels.

---

## 14. Future Development Roadmap

1. **ABDM Milestone M1–M3 Compliance:** Full integration with Ayushman Bharat Digital Mission (ABDM) sandbox for official ABHA creation, linking, and FHIR-compliant Health Information Exchange.
2. **Hospital Information Management System (HIMS) HL7/FHIR Connectors:** Direct bidirectional synchronization with enterprise hospital EMR systems (Epic, Cerner, Bahmni).
3. **Automated Cashless Pre-Authorization Claims:** Direct API linkage with the National Health Authority (NHA) TMS portal and private insurance Third Party Administrators (TPAs).
4. **Multilingual Regional Speech Models:** Fine-tuned regional Indian language automated speech recognition (Bhashini AI / Whisper Hindi, Marathi, Tamil, Telugu).
5. **PostgreSQL Multi-Region Staging Deployment:** Distributed staging container deployment with automated database failover.

---

## 15. License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
