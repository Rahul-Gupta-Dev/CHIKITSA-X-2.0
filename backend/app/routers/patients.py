from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.auth import get_current_user, get_current_user_optional
from app.models.user import UserModel
from app.models.consent import ConsentLogModel
from app.models.patient import PatientModel
from app.models.medical_record import MedicalRecordModel
from app.models.intake import IntakeSessionModel
from app.models.triage import TriageResultModel
from app.schemas import PatientProfileCreate, PatientProfileUpdate, PatientProfileOut

router = APIRouter(prefix="/api/patients", tags=["Patients"])

def patient_to_dict(p: PatientModel) -> Dict[str, Any]:
    return {
        "id": p.id,
        "userId": p.user_id,
        "fullName": p.full_name,
        "age": p.age,
        "gender": p.gender,
        "bloodGroup": p.blood_group,
        "phone": p.phone,
        "email": p.email,
        "address": p.address,
        "city": p.city,
        "pincode": p.pincode,
        "emergencyContact": p.emergency_contact,
        "symptoms": p.symptoms or [],
        "medicalHistory": p.medical_history or [],
        "medications": p.medications or [],
        "allergies": p.allergies or [],
        "vitalSigns": p.vital_signs,
        "careStage": p.care_stage,
        "financialBudgetPreference": p.financial_budget_preference,
        "hasInsurance": p.has_insurance,
        "insuranceProvider": p.insurance_provider,
        "policyNumber": p.policy_number,
        "hasGovernmentCard": p.has_government_card,
        "rationCardType": p.ration_card_type,
        "incomeCategory": p.income_category
    }

@router.get("/{patient_id}")
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if patient_id.lower() == "me":
        if not current_user or not isinstance(current_user, UserModel):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access patient profiles."
            )
        patient = db.query(PatientModel).filter(
            (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
        ).first()
    else:
        patient = db.query(PatientModel).filter(
            (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
        ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    if not current_user or not isinstance(current_user, UserModel):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access patient profiles."
        )

    if current_user.role == "PATIENT":
        if current_user.id != patient.user_id and current_user.id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You are not authorized to view another patient's profile."
            )
    elif current_user.role == "DOCTOR":
        has_consent = db.query(ConsentLogModel).filter(
            (ConsentLogModel.patient_id == patient.id) | (ConsentLogModel.patient_id == patient.user_id),
            ConsentLogModel.status == "GRANTED"
        ).first()
        if not has_consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Active clinical consent from patient is required before accessing profile."
            )

    return patient_to_dict(patient)

@router.post("")
def create_patient(
    payload: PatientProfileCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role == "PATIENT":
        if payload.userId and payload.userId != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot create a patient profile for another user."
            )
        target_user_id = current_user.id
    elif current_user.role in ["HOSPITAL_ADMIN", "ADMIN"]:
        target_user_id = payload.userId or current_user.id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Unauthorized role to create patient profiles."
        )

    patient_id = payload.id or f"pat-{payload.fullName.lower().replace(' ', '-')}-1"
    patient = PatientModel(
        id=patient_id,
        user_id=target_user_id,
        full_name=payload.fullName,
        age=payload.age,
        gender=payload.gender,
        blood_group=payload.bloodGroup,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        city=payload.city,
        pincode=payload.pincode,
        emergency_contact=payload.emergencyContact.dict() if payload.emergencyContact else None,
        symptoms=payload.symptoms,
        medical_history=payload.medicalHistory,
        medications=payload.medications,
        allergies=payload.allergies,
        vital_signs=payload.vitalSigns,
        care_stage=payload.careStage,
        financial_budget_preference=payload.financialBudgetPreference,
        has_insurance=payload.hasInsurance,
        insurance_provider=payload.insuranceProvider,
        policy_number=payload.policyNumber,
        has_government_card=payload.hasGovernmentCard,
        ration_card_type=payload.rationCardType,
        income_category=payload.incomeCategory
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient_to_dict(patient)

@router.put("/{patient_id}")
def update_patient(
    patient_id: str,
    payload: PatientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if patient_id.lower() == "me":
        if not current_user or not isinstance(current_user, UserModel):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to modify patient profile."
            )
        patient = db.query(PatientModel).filter(
            (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
        ).first()
    else:
        patient = db.query(PatientModel).filter(
            (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
        ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to modify patient profile."
        )

    if isinstance(current_user, UserModel) and current_user.role == "PATIENT":
        if current_user.id != patient.user_id and current_user.id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot modify another patient's profile."
            )

    update_data = payload.dict(exclude_unset=True)

    # Patient Care-Stage Integrity: Prevent arbitrary client-side care stage changes/skips/regressions
    if "careStage" in update_data and update_data["careStage"] is not None:
        if update_data["careStage"] != patient.care_stage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arbitrary care_stage modification is forbidden. Care stage is server-controlled and advances only through verified clinical workflow milestones."
            )
        del update_data["careStage"]

    if "care_stage" in update_data:
        del update_data["care_stage"]

    mapping = {
        "fullName": "full_name",
        "bloodGroup": "blood_group",
        "hasInsurance": "has_insurance",
        "insuranceProvider": "insurance_provider",
        "policyNumber": "policy_number",
        "hasGovernmentCard": "has_government_card",
        "rationCardType": "ration_card_type",
        "incomeCategory": "income_category",
        "medicalHistory": "medical_history",
        "emergencyContact": "emergency_contact"
    }
    for key, val in update_data.items():
        db_key = mapping.get(key, key)
        setattr(patient, db_key, val)

    db.commit()
    db.refresh(patient)
    return patient_to_dict(patient)

@router.get("/{patient_id}/profile")
def get_unified_patient_profile(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if patient_id.lower() == "me":
        if not current_user or not isinstance(current_user, UserModel):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view patient profile."
            )
        patient = db.query(PatientModel).filter(
            (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
        ).first()
    else:
        patient = db.query(PatientModel).filter(
            (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
        ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view patient profile."
        )

    if isinstance(current_user, UserModel):
        if current_user.role == "PATIENT":
            if current_user.id != patient.user_id and current_user.id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You are not authorized to view another patient's profile."
                )
        elif current_user.role == "DOCTOR":
            has_consent = db.query(ConsentLogModel).filter(
                (ConsentLogModel.patient_id == patient.id) | (ConsentLogModel.patient_id == patient.user_id),
                ConsentLogModel.status == "GRANTED"
            ).first()
            if not has_consent:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Active clinical consent from patient is required before accessing profile."
                )

    records = db.query(MedicalRecordModel).filter(MedicalRecordModel.patient_id == patient.id).all()
    latest_intake = db.query(IntakeSessionModel).filter(IntakeSessionModel.patient_id == patient.id).order_by(IntakeSessionModel.timestamp.desc()).first()
    latest_triage = db.query(TriageResultModel).filter(TriageResultModel.patient_id == patient.id).order_by(TriageResultModel.timestamp.desc()).first()

    profile_dict = patient_to_dict(patient)
    profile_dict["previousRecordsCount"] = len(records)
    profile_dict["medicalRecords"] = [
        {
            "id": r.id,
            "patientId": r.patient_id,
            "fileName": r.file_name,
            "fileType": r.file_type,
            "category": r.category,
            "uploadDate": r.upload_date,
            "ocrExtractedData": r.ocr_extracted_data,
            "isVerifiedByPatient": r.is_verified_by_patient
        }
        for r in records
    ]
    profile_dict["latestIntake"] = {
        "id": latest_intake.id,
        "transcript": latest_intake.raw_transcript,
        "symptoms": latest_intake.extracted_symptoms,
        "severity": latest_intake.severity
    } if latest_intake else None

    profile_dict["latestTriage"] = {
        "id": latest_triage.id,
        "riskLevel": latest_triage.risk_level,
        "urgency": latest_triage.urgency,
        "recommendedSpecialty": latest_triage.recommended_specialty
    } if latest_triage else None

    return profile_dict

@router.get("/{patient_id}/records")
def get_patient_records(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view patient records."
        )

    curr_patient = db.query(PatientModel).filter(
        (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
    ).first()

    if patient_id.lower() == "me":
        patient = curr_patient
        patient_id = current_user.id
    else:
        patient = db.query(PatientModel).filter(
            (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
        ).first()

    if isinstance(current_user, UserModel):
        if current_user.role == "PATIENT":
            valid_ids = [current_user.id]
            if curr_patient:
                valid_ids.append(curr_patient.id)
                if curr_patient.user_id:
                    valid_ids.append(curr_patient.user_id)
            if patient_id not in valid_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You cannot access medical records belonging to another patient."
                )
        elif current_user.role == "DOCTOR":
            p_ids = [patient_id]
            if patient:
                p_ids.extend([patient.id, patient.user_id])
            active_consent = db.query(ConsentLogModel).filter(
                ConsentLogModel.patient_id.in_(p_ids),
                ConsentLogModel.status == "GRANTED"
            ).first()
            if not active_consent:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Active patient consent is required to access medical records."
                )

    records = db.query(MedicalRecordModel).filter(
        (MedicalRecordModel.patient_id == patient_id) |
        (MedicalRecordModel.patient_id == (patient.id if patient else "")) |
        (MedicalRecordModel.patient_id == (patient.user_id if patient else ""))
    ).all()
    return [
        {
            "id": r.id,
            "patientId": r.patient_id,
            "fileName": r.file_name,
            "fileType": r.file_type,
            "category": r.category,
            "uploadDate": r.upload_date,
            "ocrExtractedData": r.ocr_extracted_data,
            "isVerifiedByPatient": r.is_verified_by_patient
        }
        for r in records
    ]
