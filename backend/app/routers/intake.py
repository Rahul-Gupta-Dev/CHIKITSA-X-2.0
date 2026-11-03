import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user_optional
from app.models.user import UserModel
from app.models.intake import IntakeSessionModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.models.consultation import ConsultationModel
from app.models.consent import ConsentLogModel
from app.schemas import IntakeRequest, IntakeResponse
from app.services.voice_intake_service import VoiceIntakeService

router = APIRouter(prefix="/api/intake", tags=["Voice Intake"])

def get_patient_valid_ids(patient_id: str, db: Session) -> set:
    valid_ids = {patient_id}
    pat = db.query(PatientModel).filter(
        (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
    ).first()
    if pat:
        valid_ids.add(pat.id)
        if pat.user_id:
            valid_ids.add(pat.user_id)
    user_pat = db.query(UserModel).filter(UserModel.id == patient_id).first()
    if user_pat:
        valid_ids.add(user_pat.id)
    return valid_ids

def check_doctor_authorization_for_patient(current_user: UserModel, valid_patient_ids: set, db: Session) -> bool:
    valid_doctor_ids = {current_user.id}
    matching_docs = db.query(DoctorModel).filter(
        (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
    ).all()
    for md in matching_docs:
        valid_doctor_ids.add(md.id)

    # 1. Appointment
    has_opd = db.query(OPDAppointmentModel).filter(
        OPDAppointmentModel.patient_id.in_(list(valid_patient_ids)),
        (OPDAppointmentModel.doctor_id.in_(list(valid_doctor_ids)) | (OPDAppointmentModel.doctor_name == current_user.name))
    ).first()
    if has_opd:
        return True

    # 2. Consultation
    has_cons = db.query(ConsultationModel).filter(
        ConsultationModel.patient_id.in_(list(valid_patient_ids)),
        (ConsultationModel.doctor_id.in_(list(valid_doctor_ids)) | (ConsultationModel.doctor_name == current_user.name))
    ).first()
    if has_cons:
        return True

    # 3. Active Consent
    has_cst = db.query(ConsentLogModel).filter(
        ConsentLogModel.patient_id.in_(list(valid_patient_ids)),
        (ConsentLogModel.doctor_id.in_(list(valid_doctor_ids)) | (ConsentLogModel.doctor_name == current_user.name)),
        ConsentLogModel.status == "GRANTED"
    ).first()
    if has_cst:
        return True

    return False

def format_intake_response(intake: IntakeSessionModel) -> Dict[str, Any]:
    iso_time = intake.timestamp.isoformat() if intake.timestamp else datetime.datetime.utcnow().isoformat()
    return {
        "id": intake.id,
        "patient_id": intake.patient_id,
        "patientId": intake.patient_id,
        "timestamp": iso_time,
        "raw_transcript": intake.raw_transcript,
        "rawTranscript": intake.raw_transcript,
        "extracted_symptoms": intake.extracted_symptoms or [],
        "extractedSymptoms": intake.extracted_symptoms or [],
        "duration": intake.duration or "Recent",
        "severity": intake.severity or "Moderate",
        "affected_body_part": intake.affected_body_part,
        "affectedBodyPart": intake.affected_body_part,
        "trigger_event": intake.trigger_event,
        "triggerEvent": intake.trigger_event,
        "is_emergency_alert": bool(intake.is_emergency_alert),
        "isEmergencyAlert": bool(intake.is_emergency_alert),
        "disclaimer": "AI-assisted symptom extraction only. Clinical evaluation by a licensed physician is required."
    }

@router.post("", response_model=IntakeResponse)
@router.post("/", response_model=IntakeResponse)
def submit_intake(
    payload: IntakeRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to submit clinical intake."
        )

    raw_transcript = (payload.transcript or payload.raw_transcript or payload.rawTranscript or "").strip()
    if not raw_transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice transcript or symptom text cannot be empty."
        )

    if len(raw_transcript) > 5000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcript exceeds maximum permitted length of 5000 characters."
        )

    client_pid = (payload.patient_id or payload.patientId or "").strip()

    # Enforce RBAC and IDOR protection
    if current_user.role == "PATIENT":
        user_pids = get_patient_valid_ids(current_user.id, db)
        if client_pid and client_pid not in user_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Patients can only submit clinical intake for their own health profile."
            )
        target_patient_id = client_pid if client_pid in user_pids else current_user.id
    elif current_user.role == "DOCTOR":
        if not client_pid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id is required for doctor-assisted intake."
            )
        valid_pids = get_patient_valid_ids(client_pid, db)
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized for this patient."
            )
        target_patient_id = client_pid
    elif current_user.role in ("HOSPITAL_ADMIN", "HOSPITAL_STAFF", "ADMIN"):
        if not client_pid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id is required for hospital clinical intake."
            )
        target_patient_id = client_pid
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Insufficient privileges to submit clinical intake."
        )

    # Process transcript with VoiceIntakeService
    processed = VoiceIntakeService.process_transcript(raw_transcript)

    intake_id = f"intake-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    intake = IntakeSessionModel(
        id=intake_id,
        patient_id=target_patient_id,
        timestamp=datetime.datetime.utcnow(),
        raw_transcript=raw_transcript,
        extracted_symptoms=processed.get("extracted_symptoms", []),
        duration=payload.duration if payload.duration and payload.duration != "Recent" else processed.get("duration", "Recent"),
        severity=payload.severity if payload.severity and payload.severity != "Moderate" else processed.get("severity", "Moderate"),
        affected_body_part=payload.affected_body_part or payload.affectedBodyPart or processed.get("affected_body_part"),
        trigger_event=payload.trigger_event or payload.triggerEvent,
        is_emergency_alert=bool(processed.get("is_emergency_alert", False))
    )
    db.add(intake)

    # Sync symptoms and care stage to patient profile
    target_pids = get_patient_valid_ids(target_patient_id, db)
    patient = db.query(PatientModel).filter(
        (PatientModel.id.in_(list(target_pids))) | (PatientModel.user_id.in_(list(target_pids)))
    ).first()

    if patient:
        existing_symptoms = patient.symptoms or []
        new_symptoms = processed.get("extracted_symptoms", [])
        merged = list(dict.fromkeys(existing_symptoms + new_symptoms))
        patient.symptoms = merged
        if patient.care_stage is None or patient.care_stage < 2:
            patient.care_stage = 2

    db.commit()
    db.refresh(intake)

    return format_intake_response(intake)

@router.get("/patient/{patient_id}")
def get_patient_intakes(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view clinical intake records."
        )

    resolved_pid = current_user.id if patient_id in ("me", "current") else patient_id
    valid_pids = get_patient_valid_ids(resolved_pid, db)

    # Enforce RBAC
    if current_user.role == "PATIENT":
        if current_user.id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access intake records of another patient."
            )
    elif current_user.role == "DOCTOR":
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized for this patient."
            )
    elif current_user.role in ("HOSPITAL_ADMIN", "HOSPITAL_STAFF", "ADMIN"):
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Insufficient privileges."
        )

    intakes = db.query(IntakeSessionModel).filter(
        IntakeSessionModel.patient_id.in_(list(valid_pids))
    ).order_by(IntakeSessionModel.timestamp.desc()).all()

    return [format_intake_response(i) for i in intakes]
