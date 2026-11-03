import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.auth import get_current_user_optional
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.consent import ConsentLogModel
from app.schemas import ConsentCreateRequest, ConsentOut

router = APIRouter(prefix="/api/consent", tags=["Patient Access Consent"])

def consent_to_dict(c: ConsentLogModel) -> Dict[str, Any]:
    return {
        "id": c.id,
        "patientId": c.patient_id,
        "hospitalId": c.hospital_id,
        "hospitalName": c.hospital_name,
        "doctorId": c.doctor_id,
        "doctorName": c.doctor_name,
        "status": c.status,
        "accessibleSections": c.accessible_sections or []
    }

@router.post("", response_model=ConsentOut)
def record_consent(
    payload: ConsentCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to grant or update consent."
        )

    patient_id = payload.patient_id or payload.patientId or "me"
    hospital_id = payload.hospital_id or payload.hospitalId or "hosp-1"
    hospital_name = payload.hospital_name or payload.hospitalName or "CarePlus Super Specialty Hospital"
    doctor_id = payload.doctor_id or payload.doctorId
    doctor_name = payload.doctor_name or payload.doctorName

    # 1. Enforce Patient-Only Consent Granting
    if payload.granted:
        if current_user.role != "PATIENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only authenticated patients can grant medical record consent. Doctors and hospital staff cannot approve consent."
            )

        if patient_id.lower() == "me":
            patient_id = current_user.id

        patient = db.query(PatientModel).filter(
            (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
        ).first()
        valid_ids = [current_user.id]
        if patient:
            valid_ids.append(patient.id)
            if patient.user_id:
                valid_ids.append(patient.user_id)
        valid_ids = list(set(filter(None, valid_ids)))

        if patient_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot grant consent on behalf of another patient."
            )

        # Look up existing PENDING or REVOKED consent to grant
        existing = db.query(ConsentLogModel).filter(
            ConsentLogModel.patient_id.in_(valid_ids),
            ConsentLogModel.hospital_id == hospital_id,
            ConsentLogModel.status.in_(["PENDING", "REVOKED"])
        ).order_by(ConsentLogModel.requested_at.desc()).first()

        if existing:
            existing.status = "GRANTED"
            existing.granted_at = datetime.datetime.utcnow()
            if doctor_id:
                existing.doctor_id = doctor_id
            if doctor_name:
                existing.doctor_name = doctor_name
            db.commit()
            db.refresh(existing)
            return consent_to_dict(existing)

        # If already active GRANTED
        active = db.query(ConsentLogModel).filter(
            ConsentLogModel.patient_id.in_(valid_ids),
            ConsentLogModel.hospital_id == hospital_id,
            ConsentLogModel.status == "GRANTED"
        ).first()
        if active:
            return consent_to_dict(active)

        # Proactive grant
        cst_id = f"cst-{int(datetime.datetime.utcnow().timestamp()*1000)}"
        consent = ConsentLogModel(
            id=cst_id,
            patient_id=current_user.id,
            hospital_id=hospital_id,
            hospital_name=hospital_name,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            requested_at=datetime.datetime.utcnow(),
            granted_at=datetime.datetime.utcnow(),
            status="GRANTED",
            accessible_sections=["PROFILE", "SYMPTOMS", "OCR_RECORDS", "TRIAGE"]
        )
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent_to_dict(consent)

    else:
        # Access request (status = PENDING only)
        if patient_id.lower() == "me":
            if current_user.role == "PATIENT":
                patient_id = current_user.id
            else:
                raise HTTPException(status_code=400, detail="Explicit patient ID required for staff consent requests.")

        target_patient = db.query(PatientModel).filter(
            (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
        ).first()
        if not target_patient:
            user_check = db.query(UserModel).filter(UserModel.id == patient_id).first()
            if not user_check:
                raise HTTPException(status_code=404, detail="Target patient record not found.")

        target_valid_ids = [patient_id]
        if target_patient:
            target_valid_ids.extend([target_patient.id, target_patient.user_id])
        target_valid_ids = list(set(filter(None, target_valid_ids)))

        existing = db.query(ConsentLogModel).filter(
            ConsentLogModel.patient_id.in_(target_valid_ids),
            ConsentLogModel.hospital_id == hospital_id
        ).order_by(ConsentLogModel.requested_at.desc()).first()

        if existing:
            if existing.status in ["PENDING", "GRANTED"]:
                return consent_to_dict(existing)
            # If previously REVOKED, a new request moves it to PENDING
            existing.status = "PENDING"
            existing.requested_at = datetime.datetime.utcnow()
            existing.granted_at = None
            if doctor_id:
                existing.doctor_id = doctor_id
            if doctor_name:
                existing.doctor_name = doctor_name
            db.commit()
            db.refresh(existing)
            return consent_to_dict(existing)

        cst_id = f"cst-{int(datetime.datetime.utcnow().timestamp()*1000)}"
        consent = ConsentLogModel(
            id=cst_id,
            patient_id=patient_id,
            hospital_id=hospital_id,
            hospital_name=hospital_name,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            requested_at=datetime.datetime.utcnow(),
            granted_at=None,
            status="PENDING",
            accessible_sections=["PROFILE", "SYMPTOMS", "OCR_RECORDS", "TRIAGE"]
        )
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent_to_dict(consent)

@router.get("/{patient_id}", response_model=List[ConsentOut])
def get_patient_consents(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view consent records."
        )

    if patient_id.lower() == "me":
        patient_id = current_user.id

    patient = db.query(PatientModel).filter(
        (PatientModel.user_id == patient_id) | (PatientModel.id == patient_id)
    ).first()
    valid_ids = [patient_id]
    if patient:
        valid_ids.extend([patient.id, patient.user_id])
    valid_ids = list(set(filter(None, valid_ids)))

    if isinstance(current_user, UserModel) and current_user.role == "PATIENT":
        current_valid_ids = [current_user.id]
        cur_patient = db.query(PatientModel).filter(
            (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
        ).first()
        if cur_patient:
            current_valid_ids.extend([cur_patient.id, cur_patient.user_id])
        current_valid_ids = list(set(filter(None, current_valid_ids)))

        if patient_id not in current_valid_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot view consents belonging to another patient."
            )

    consents = db.query(ConsentLogModel).filter(
        ConsentLogModel.patient_id.in_(valid_ids)
    ).all()
    return [consent_to_dict(c) for c in consents]

@router.put("/{consent_id}/revoke", response_model=ConsentOut)
def revoke_consent(
    consent_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    consent = db.query(ConsentLogModel).filter(ConsentLogModel.id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to revoke consent."
        )

    if current_user.role != "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only patients can revoke their medical record consent."
        )

    patient = db.query(PatientModel).filter(
        (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
    ).first()
    valid_ids = [current_user.id]
    if patient:
        valid_ids.append(patient.id)
        if patient.user_id:
            valid_ids.append(patient.user_id)
    valid_ids = list(set(filter(None, valid_ids)))

    if consent.patient_id not in valid_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot revoke another patient's consent."
        )

    consent.status = "REVOKED"
    db.commit()
    db.refresh(consent)
    return consent_to_dict(consent)
