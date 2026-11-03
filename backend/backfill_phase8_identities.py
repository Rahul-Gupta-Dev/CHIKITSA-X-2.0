import os
import sys
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(CURRENT_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.database import build_engine, normalize_database_url
from app.models.user import UserModel
from app.models.doctor import DoctorModel
from app.models.patient import PatientModel
from sqlalchemy.orm import sessionmaker

def generate_public_id(user_id: str, role: str, index: int = 0) -> str:
    role_prefix = {
        "PATIENT": "P",
        "DOCTOR": "D",
        "HOSPITAL_ADMIN": "H",
        "HOSPITAL_STAFF": "S",
        "RECEPTIONIST": "S",
        "SUPER_ADMIN": "A"
    }.get(role.upper(), "U")

    if user_id == "usr-patient-1":
        return "CHX-P-00000001"
    elif user_id == "usr-doctor-1":
        return "CHX-D-00000001"
    elif user_id == "usr-hospital-1":
        return "CHX-H-00000001"

    # Deterministic yet collision-resistant 8-char uppercase hex derived from user_id + index
    seed = f"{user_id}:{role}:{index}".encode("utf-8")
    hash_hex = hashlib.sha256(seed).hexdigest()[:8].upper()
    return f"CHX-{role_prefix}-{hash_hex}"

def run_backfill():
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        print("[ERROR] DATABASE_URL is not set.")
        sys.exit(1)

    print("=" * 80)
    print("CHIKITSA-X 2.0: BACKFILLING IDENTITIES, PUBLIC IDs & MAPPING DOCTORS")
    print("=" * 80)

    engine = build_engine(normalize_database_url(raw_url))
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    assigned_public_ids = set()
    mapping_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_users": 0,
        "users_by_status": {},
        "mapped_doctors": [],
        "unresolved_doctors": [],
        "demo_accounts_audit": []
    }

    with Session() as session:
        # 1. Backfill Users
        users = session.query(UserModel).order_by(UserModel.created_at, UserModel.id).all()
        mapping_report["total_users"] = len(users)
        print(f"\n[1] Processing {len(users)} users for public_id and account_status...")

        # Find patients with linked patient profiles
        patient_profile_user_ids = set(
            row[0] for row in session.query(PatientModel.user_id).all()
        )

        for u in users:
            # Generate unique public_id if missing
            if not u.public_id:
                idx = 0
                while True:
                    candidate = generate_public_id(u.id, u.role, idx)
                    if candidate not in assigned_public_ids:
                        u.public_id = candidate
                        assigned_public_ids.add(candidate)
                        break
                    idx += 1
            else:
                assigned_public_ids.add(u.public_id)

            # Account status & approval policy
            if u.id == "usr-patient-1":
                u.account_status = "ACTIVE"
                u.approval_status = "APPROVED"
                u.email_verified = True
                u.phone_verified = True
                u.approved_by = "SYSTEM_INITIAL_SEED"
                u.approved_at = u.created_at
                mapping_report["demo_accounts_audit"].append({
                    "id": u.id, "email": u.email, "role": u.role, "status": u.account_status, "public_id": u.public_id
                })
            elif u.id == "usr-doctor-1":
                u.account_status = "ACTIVE"
                u.approval_status = "APPROVED"
                u.email_verified = True
                u.phone_verified = True
                u.approved_by = "SYSTEM_INITIAL_SEED"
                u.approved_at = u.created_at
                mapping_report["demo_accounts_audit"].append({
                    "id": u.id, "email": u.email, "role": u.role, "status": u.account_status, "public_id": u.public_id
                })
            elif u.id == "usr-hospital-1":
                u.account_status = "ACTIVE"
                u.approval_status = "APPROVED"
                u.email_verified = True
                u.phone_verified = True
                u.approved_by = "SYSTEM_INITIAL_SEED"
                u.approved_at = u.created_at
                mapping_report["demo_accounts_audit"].append({
                    "id": u.id, "email": u.email, "role": u.role, "status": u.account_status, "public_id": u.public_id
                })
            elif u.role == "PATIENT":
                # Registered patients with active profile
                if u.id in patient_profile_user_ids:
                    u.account_status = "ACTIVE"
                    u.approval_status = "APPROVED"
                    u.email_verified = True
                    u.phone_verified = bool(u.phone)
                    u.approved_by = "PATIENT_AUTO_PROVISION"
                    u.approved_at = u.created_at
                else:
                    u.account_status = "PENDING_VERIFICATION"
                    u.approval_status = "PENDING"
            elif u.role == "DOCTOR":
                # Unverified / test doctor accounts must NOT be automatically active
                u.account_status = "PENDING_APPROVAL"
                u.approval_status = "PENDING"
                u.email_verified = True
            elif u.role in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF", "RECEPTIONIST"]:
                u.account_status = "PENDING_APPROVAL"
                u.approval_status = "PENDING"
            else:
                u.account_status = "PENDING_APPROVAL"
                u.approval_status = "PENDING"

            mapping_report["users_by_status"][u.account_status] = mapping_report["users_by_status"].get(u.account_status, 0) + 1

        session.commit()
        print(f"  [PASS] All {len(users)} users backfilled with unique public_id and validated account_status.")
        print(f"         Account Status Breakdown: {mapping_report['users_by_status']}")

        # 2. Map Doctor Identities
        print("\n[2] Verifying Doctor Identities and Linking DoctorModel.user_id...")
        doctors = session.query(DoctorModel).all()
        for doc in doctors:
            # Check verified mapping for doc-1 -> usr-doctor-1
            if doc.id == "doc-1":
                user_doc = session.query(UserModel).filter_by(id="usr-doctor-1").first()
                if user_doc and user_doc.name == doc.name and user_doc.hospital_id == doc.hospital_id:
                    doc.user_id = user_doc.id
                    doc.medical_registration_number = "MCI-2015-48291"
                    doc.verification_status = "VERIFIED"
                    mapping_report["mapped_doctors"].append({
                        "doctor_id": doc.id,
                        "doctor_name": doc.name,
                        "hospital_id": doc.hospital_id,
                        "user_id": user_doc.id,
                        "user_email": user_doc.email,
                        "medical_reg_no": doc.medical_registration_number,
                        "verification_status": doc.verification_status
                    })
                    print(f"  • [VERIFIED MAP] Doctor '{doc.id}' ({doc.name}) -> User '{user_doc.id}' ({user_doc.email})")
            elif doc.id == "doc-2":
                # Multiple test accounts exist with name 'Dr. Ananya Roy' from automated regression tests.
                # Per strict policy: Do NOT guess mappings. Report as unresolved for manual review.
                doc.user_id = None
                doc.medical_registration_number = "MCI-2018-73910"
                doc.verification_status = "PENDING_CREDENTIAL_LINK"
                matching_test_users = [
                    {"id": u.id, "email": u.email}
                    for u in users if "Ananya Roy" in u.name
                ]
                mapping_report["unresolved_doctors"].append({
                    "doctor_id": doc.id,
                    "doctor_name": doc.name,
                    "hospital_id": doc.hospital_id,
                    "status": "UNRESOLVED_MANUAL_REVIEW_REQUIRED",
                    "reason": f"Found {len(matching_test_users)} test accounts with matching name. No certified primary user designated.",
                    "potential_candidates": matching_test_users[:5]
                })
                print(f"  • [UNRESOLVED] Doctor '{doc.id}' ({doc.name}) retained with user_id=NULL (Awaiting manual administrative linking)")

        session.commit()

    engine.dispose()

    # Save mapping report
    out_path = os.path.join(CURRENT_DIR, "identity_mapping_audit_report.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(mapping_report, fh, indent=2)

    print("\n" + "=" * 80)
    print("IDENTITY BACKFILL & DOCTOR MAPPING COMPLETE")
    print(f"Report saved to: {out_path}")
    print("=" * 80)
    return mapping_report

if __name__ == "__main__":
    run_backfill()
