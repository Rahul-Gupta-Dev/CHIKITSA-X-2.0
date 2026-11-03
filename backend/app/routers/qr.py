import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_current_user_optional
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.opd import OPDAppointmentModel
from app.models.qr import QRReferenceModel
from typing import Union, Optional
from app.schemas import QRGenerateRequest, QRVerifyResponse, HospitalVerifyRequest

router = APIRouter(prefix="/api", tags=["QR & Verification"])

@router.post("/qr")
def generate_qr(payload: Union[QRGenerateRequest, dict, None] = None, appointment_id: str = None, db: Session = Depends(get_db)):
    app_id = appointment_id
    if not app_id and payload:
        if isinstance(payload, QRGenerateRequest):
            app_id = payload.appointment_id
        elif isinstance(payload, dict):
            app_id = payload.get("appointment_id") or payload.get("appointmentId")

    if not app_id:
        raise HTTPException(status_code=400, detail="appointment_id is required")

    opd = db.query(OPDAppointmentModel).filter(
        (OPDAppointmentModel.id == app_id) | (OPDAppointmentModel.reference_id == app_id)
    ).first()
    if not opd:
        raise HTTPException(status_code=404, detail="Appointment not found")

    qr = db.query(QRReferenceModel).filter(QRReferenceModel.reference_id == opd.reference_id).first()
    if not qr:
        qr = QRReferenceModel(
            id=f"qr-{opd.id}",
            reference_id=opd.reference_id,
            token=opd.qr_token,
            patient_id=opd.patient_id,
            hospital_id=opd.hospital_id,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            is_verified=False
        )
        db.add(qr)
        db.commit()
        db.refresh(qr)

    return {
        "id": qr.id,
        "reference_id": qr.reference_id,
        "secure_token": qr.token,
        "qr_payload": f"CHIKITSAX_SECURE_PASS:{qr.reference_id}:{qr.token}",
        "expires_at": qr.expires_at.isoformat()
    }

@router.get("/qr/verify/{reference_id}", response_model=QRVerifyResponse)
def verify_qr(reference_id: str, db: Session = Depends(get_db)):
    clean_ref = reference_id.strip().upper()
    opd = db.query(OPDAppointmentModel).filter(
        OPDAppointmentModel.reference_id == clean_ref
    ).first()

    if not opd:
        return {
            "verified": False,
            "message": f"Reference ID {clean_ref} not found"
        }

    return {
        "verified": True,
        "message": f"Appointment verified for {opd.patient_name}",
        "reference_id": opd.reference_id,
        "hospital": opd.hospital_name,
        "department": opd.department,
        "doctor": opd.doctor_name,
        "appointment_date": opd.appointment_date,
        "appointment_time": opd.appointment_time,
        "status": opd.status.lower(),
        "appointment": {
            "id": opd.id,
            "referenceId": opd.reference_id,
            "patientId": opd.patient_id,
            "patientName": opd.patient_name,
            "patientPhone": opd.patient_phone,
            "hospitalId": opd.hospital_id,
            "hospitalName": opd.hospital_name,
            "department": opd.department,
            "doctorId": opd.doctor_id,
            "doctorName": opd.doctor_name,
            "appointmentDate": opd.appointment_date,
            "appointmentTime": opd.appointment_time,
            "status": opd.status
        }
    }

@router.post("/hospital/verify", response_model=QRVerifyResponse)
def hospital_staff_verify(
    payload: HospitalVerifyRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # 1. Enforce strict role authorization: allow only HOSPITAL_ADMIN or HOSPITAL_STAFF
    if current_user.role not in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only hospital staff can perform check-in."
        )

    clean_ref = payload.reference_id.strip().upper()
    opd = db.query(OPDAppointmentModel).filter(
        OPDAppointmentModel.reference_id == clean_ref
    ).first()

    if not opd:
        return {
            "verified": False,
            "message": f"Reference ID {clean_ref} not found in hospital system."
        }

    # 2. Enforce Hospital Scoping Check
    if current_user.hospital_id and current_user.hospital_id != opd.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: This appointment is booked at {opd.hospital_name} (ID: {opd.hospital_id}), not your hospital (ID: {current_user.hospital_id}). Cross-hospital verification rejected."
        )

    if payload.hospital_id and payload.hospital_id != opd.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Hospital mismatch. Appointment is for {opd.hospital_name}."
        )

    # 2. Cancelled Appointment Guard
    if opd.status == "CANCELLED":
        return {
            "verified": False,
            "message": f"Cannot verify appointment {clean_ref}: Appointment was CANCELLED by the patient.",
            "reference_id": opd.reference_id,
            "status": "CANCELLED"
        }

    qr = db.query(QRReferenceModel).filter(QRReferenceModel.reference_id == clean_ref).first()

    # 3. QR Token Expiry Guard
    if qr and qr.expires_at and qr.expires_at < datetime.datetime.utcnow():
        return {
            "verified": False,
            "message": f"Security Alert: QR appointment token for {clean_ref} has EXPIRED. Please report to registration desk.",
            "reference_id": opd.reference_id,
            "status": "EXPIRED"
        }

    # 4. QR Token Replay / Double Check-in Guard
    if opd.status in ["VERIFIED", "COMPLETED"] or (qr and qr.is_verified):
        return {
            "verified": False,
            "message": f"Security Replay Alert: Appointment {clean_ref} has ALREADY been verified on check-in. Passes cannot be reused.",
            "reference_id": opd.reference_id,
            "status": opd.status
        }

    opd.status = "VERIFIED"

    # Monotonically advance patient care stage to Stage 7 (Hospital Check-in)
    patient = db.query(PatientModel).filter(
        (PatientModel.id == opd.patient_id) | (PatientModel.user_id == opd.patient_id)
    ).first()
    if patient and (patient.care_stage is None or patient.care_stage < 7):
        patient.care_stage = 7

    if qr:
        qr.is_verified = True
        qr.verified_at = datetime.datetime.utcnow()
        qr.verified_by_staff = payload.staff_name or (current_user.name if current_user else "Reception Desk Staff")

    db.commit()
    db.refresh(opd)

    return {
        "verified": True,
        "message": f"Staff Check-in Verified for patient {opd.patient_name}",
        "reference_id": opd.reference_id,
        "hospital": opd.hospital_name,
        "department": opd.department,
        "doctor": opd.doctor_name,
        "appointment_date": opd.appointment_date,
        "appointment_time": opd.appointment_time,
        "status": opd.status,
        "appointment": {
            "id": opd.id,
            "referenceId": opd.reference_id,
            "patientId": opd.patient_id,
            "patientName": opd.patient_name,
            "patientPhone": opd.patient_phone,
            "hospitalId": opd.hospital_id,
            "hospitalName": opd.hospital_name,
            "department": opd.department,
            "doctorId": opd.doctor_id,
            "doctorName": opd.doctor_name,
            "appointmentDate": opd.appointment_date,
            "appointmentTime": opd.appointment_time,
            "status": opd.status
        }
    }
