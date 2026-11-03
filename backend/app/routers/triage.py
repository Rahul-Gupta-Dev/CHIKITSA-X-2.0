import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user_optional
from app.models.user import UserModel
from app.models.triage import TriageResultModel
from app.models.patient import PatientModel
from app.models.intake import IntakeSessionModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.models.consultation import ConsultationModel
from app.models.consent import ConsentLogModel
from app.schemas import TriageRequest, TriageResponse
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api/triage", tags=["Clinical Triage"])

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

def format_triage_response(triage: TriageResultModel) -> Dict[str, Any]:
    iso_time = triage.timestamp.isoformat() if triage.timestamp else datetime.datetime.utcnow().isoformat()
    return {
        "id": triage.id,
        "patient_id": triage.patient_id,
        "patientId": triage.patient_id,
        "timestamp": iso_time,
        "risk_level": triage.risk_level,
        "riskLevel": triage.risk_level,
        "urgency": triage.urgency,
        "recommended_specialties": [triage.recommended_specialty],
        "recommended_specialty": triage.recommended_specialty,
        "recommendedSpecialty": triage.recommended_specialty,
        "symptoms_considered": triage.symptoms_considered or [],
        "symptomsConsidered": triage.symptoms_considered or [],
        "reasoning": triage.clinical_reasoning or [],
        "clinical_reasoning": triage.clinical_reasoning or [],
        "clinicalReasoning": triage.clinical_reasoning or [],
        "next_action": triage.recommended_next_step,
        "recommended_next_step": triage.recommended_next_step,
        "recommendedNextStep": triage.recommended_next_step,
        "is_emergency_triggered": bool(triage.is_emergency_triggered),
        "isEmergencyTriggered": bool(triage.is_emergency_triggered),
        "disclaimer": "AI-assisted triage decision support only. Professional medical evaluation by a licensed physician is required."
    }

@router.post("", response_model=TriageResponse)
@router.post("/", response_model=TriageResponse)
def perform_triage(
    payload: TriageRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to perform clinical triage."
        )

    client_pid = (payload.patient_id or payload.patientId or "").strip()

    # Enforce RBAC & IDOR
    if current_user.role == "PATIENT":
        user_pids = get_patient_valid_ids(current_user.id, db)
        if client_pid and client_pid not in user_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Patients can only perform clinical triage for their own health profile."
            )
        target_patient_id = client_pid if client_pid in user_pids else current_user.id
    elif current_user.role == "DOCTOR":
        if not client_pid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id is required for clinical triage."
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
                detail="patient_id is required for clinical triage."
            )
        target_patient_id = client_pid
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Insufficient privileges."
        )

    target_pids = get_patient_valid_ids(target_patient_id, db)

    # Validate intake_id if supplied
    req_intake_id = (payload.intake_id or payload.intakeId or "").strip()
    intake = None
    if req_intake_id:
        intake = db.query(IntakeSessionModel).filter(IntakeSessionModel.id == req_intake_id).first()
        if not intake:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intake session '{req_intake_id}' not found."
            )
        if intake.patient_id not in target_pids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Intake session '{req_intake_id}' does not belong to patient '{target_patient_id}'."
            )
    else:
        intake = db.query(IntakeSessionModel).filter(
            IntakeSessionModel.patient_id.in_(list(target_pids))
        ).order_by(IntakeSessionModel.timestamp.desc()).first()

    patient = db.query(PatientModel).filter(
        (PatientModel.id.in_(list(target_pids))) | (PatientModel.user_id.in_(list(target_pids)))
    ).first()

    symptoms = []
    if intake and intake.extracted_symptoms:
        symptoms = list(intake.extracted_symptoms)
    elif patient and patient.symptoms:
        symptoms = list(patient.symptoms)
    else:
        symptoms = ["General Discomfort"]

    history = []
    if patient and patient.medical_history:
        history = list(patient.medical_history)

    is_emergency = intake.is_emergency_alert if intake else False
    severity = intake.severity if intake else "Moderate"

    eval_result = TriageService.evaluate_triage(symptoms, history, is_emergency, severity)

    triage_id = f"trg-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    triage = TriageResultModel(
        id=triage_id,
        patient_id=target_patient_id,
        timestamp=datetime.datetime.utcnow(),
        risk_level=eval_result["risk_level"],
        urgency=eval_result["urgency"],
        symptoms_considered=eval_result["symptoms_considered"],
        clinical_reasoning=eval_result["clinical_reasoning"],
        recommended_specialty=eval_result["recommended_specialty"],
        recommended_next_step=eval_result["recommended_next_step"],
        is_emergency_triggered=bool(eval_result["is_emergency_triggered"])
    )
    db.add(triage)

    if patient and (patient.care_stage is None or patient.care_stage < 4):
        patient.care_stage = 4

    db.commit()
    db.refresh(triage)

    return format_triage_response(triage)

@router.get("/patient/{patient_id}")
def get_patient_triages(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view triage records."
        )

    resolved_pid = current_user.id if patient_id in ("me", "current") else patient_id
    valid_pids = get_patient_valid_ids(resolved_pid, db)

    # Enforce RBAC
    if current_user.role == "PATIENT":
        if current_user.id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access triage records of another patient."
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

    triages = db.query(TriageResultModel).filter(
        TriageResultModel.patient_id.in_(list(valid_pids))
    ).order_by(TriageResultModel.timestamp.desc()).all()

    return [format_triage_response(t) for t in triages]
