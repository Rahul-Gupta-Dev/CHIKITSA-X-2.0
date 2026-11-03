import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.limiter import safe_rate_limit
from sqlalchemy.orm import Session
from app.auth import (
    get_db,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_user_optional,
)
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.hospital import HospitalModel
from app.schemas import LoginRequest, RegisterRequest, AuthTokenResponse, UserOut

LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "30/minute")
REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "15/minute")

router = APIRouter(prefix="/api/auth", tags=["Authentication & Access Control"])

@router.post("/login", response_model=AuthTokenResponse)
@safe_rate_limit(LOGIN_RATE_LIMIT)
def login(req: LoginRequest, request: Request = None, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    user = db.query(UserModel).filter(UserModel.email.ilike(email_clean)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials or register."
        )

    # Password verification
    # If user doesn't have a password_hash yet (e.g. initial demo seed), accept default password or set it
    if user.password_hash:
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Incorrect password."
            )
    else:
        # Save password hash for future logins
        user.password_hash = hash_password(req.password)
        db.commit()

    # Server-Side Role Authority: UserModel.role is strictly authoritative.
    # Reject privilege escalation and cross-role spoofing with 403 Forbidden.
    if req.role:
        req_role_clean = req.role.strip().upper()
        # A PATIENT cannot request privileged roles (DOCTOR, HOSPITAL_ADMIN, HOSPITAL_STAFF)
        if user.role.upper() == "PATIENT" and req_role_clean != "PATIENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Role mismatch. Account role is '{user.role}'."
            )
        # A DOCTOR cannot request non-doctor roles
        elif user.role.upper() == "DOCTOR" and req_role_clean != "DOCTOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Role mismatch. Account role is '{user.role}'."
            )
        # Hospital roles: must remain within hospital staff/admin hierarchy
        elif user.role.upper() in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF"] and req_role_clean not in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Role mismatch. Account role is '{user.role}'."
            )

    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "hospital_id": user.hospital_id
    }
    access_token = create_access_token(token_data)

    user_out = UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        avatar=user.avatar,
        phone=user.phone,
        hospitalId=user.hospital_id
    )

    return AuthTokenResponse(
        accessToken=access_token,
        tokenType="Bearer",
        user=user_out
    )

@router.post("/register", response_model=AuthTokenResponse)
@safe_rate_limit(REGISTER_RATE_LIMIT)
def register(
    req: RegisterRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    target_role = (req.role or "PATIENT").strip().upper()
    if target_role != "PATIENT":
        # Privileged registration (DOCTOR, HOSPITAL_ADMIN, HOSPITAL_STAFF) requires an authenticated admin session
        if not current_user or current_user.role not in ["HOSPITAL_ADMIN", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Public registration is limited to patients. Privileged roles (DOCTOR, HOSPITAL_ADMIN, HOSPITAL_STAFF) must be provisioned by authorized hospital administration."
            )

    email_clean = req.email.strip().lower()
    existing_user = db.query(UserModel).filter(UserModel.email.ilike(email_clean)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{email_clean}' already exists. Please log in instead."
        )

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    user_name = (req.name or req.fullName or "User").strip()
    new_user = UserModel(
        id=user_id,
        email=email_clean,
        name=user_name,
        role=target_role,
        password_hash=hash_password(req.password),
        phone=req.phone,
        hospital_id=req.hospitalId
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If registering as a patient, seed a corresponding patient profile
    if new_user.role == "PATIENT":
        patient = PatientModel(
            id=f"pat-{uuid.uuid4().hex[:8]}",
            user_id=new_user.id,
            full_name=new_user.name,
            age=req.age or 30,
            gender=req.gender or "Other",
            blood_group=req.bloodGroup or "B+",
            phone=new_user.phone or "+91 99999 88888",
            email=new_user.email,
            address="Primary Residence",
            city=req.city or "New Delhi",
            pincode="110001",
            symptoms=[],
            medical_history=[],
            medications=[],
            allergies=[],
            care_stage=1,
            financial_budget_preference="MEDIUM",
            has_insurance=False
        )
        db.add(patient)
        db.commit()

    token_data = {
        "sub": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "name": new_user.name,
        "hospital_id": new_user.hospital_id
    }
    access_token = create_access_token(token_data)

    user_out = UserOut(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        avatar=new_user.avatar,
        phone=new_user.phone,
        hospitalId=new_user.hospital_id
    )

    return AuthTokenResponse(
        accessToken=access_token,
        tokenType="Bearer",
        user=user_out
    )

@router.get("/me")
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "hospitalId": current_user.hospital_id
    }

    if current_user.role == "PATIENT":
        patient = db.query(PatientModel).filter(PatientModel.user_id == current_user.id).first()
        if patient:
            profile["patientProfile"] = {
                "id": patient.id,
                "fullName": patient.full_name,
                "age": patient.age,
                "gender": patient.gender,
                "bloodGroup": patient.blood_group,
                "city": patient.city,
                "careStage": patient.care_stage,
                "hasInsurance": patient.has_insurance
            }
    elif current_user.role == "DOCTOR":
        doctor = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) |
            (DoctorModel.name == current_user.name) |
            (DoctorModel.hospital_id == current_user.hospital_id)
        ).first()
        if not doctor and current_user.id == "usr-doctor-1":
            doctor = db.query(DoctorModel).filter(DoctorModel.id == "doc-1").first()
        if doctor:
            profile["doctorProfile"] = {
                "id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty,
                "hospitalId": doctor.hospital_id,
                "experience": getattr(doctor, "experience_years", 5),
                "consultationFee": doctor.consultation_fee
            }
    elif current_user.role in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF"]:
        hospital = db.query(HospitalModel).filter(HospitalModel.id == current_user.hospital_id).first()
        if not hospital and current_user.hospital_id:
            hospital = db.query(HospitalModel).filter(HospitalModel.id == "hosp-1").first()
        if hospital:
            profile["hospitalProfile"] = {
                "id": hospital.id,
                "name": hospital.name,
                "city": hospital.city,
                "type": hospital.type
            }

    return profile
