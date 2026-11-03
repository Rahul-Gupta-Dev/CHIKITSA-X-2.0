import datetime
import random
import string
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db, SLOT_MUTATION_LOCK
from app.auth import get_current_user, get_current_user_optional
from app.models.user import UserModel
from app.models.opd import OPDAppointmentModel
from app.models.qr import QRReferenceModel
from app.models.hospital import HospitalModel
from app.models.doctor import DoctorModel
from app.models.patient import PatientModel
from app.schemas import OPDCreateRequest, OPDResponse, OPDRescheduleRequest

router = APIRouter(prefix="/api/opd", tags=["OPD Registration & Management"])

def generate_ref_id() -> str:
    chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"CHX-2026-{chars}"

def opd_to_dict(opd: OPDAppointmentModel) -> dict:
    return {
        "id": opd.id,
        "appointment_id": opd.id,
        "reference_id": opd.reference_id,
        "patient_id": opd.patient_id,
        "patient_name": opd.patient_name,
        "patient_phone": opd.patient_phone,
        "hospital_id": opd.hospital_id,
        "hospital_name": opd.hospital_name,
        "hospital": opd.hospital_name,
        "department": opd.department,
        "doctor_id": opd.doctor_id,
        "doctor_name": opd.doctor_name,
        "doctor": opd.doctor_name,
        "appointment_date": opd.appointment_date,
        "appointment_time": opd.appointment_time,
        "consultation_fee": opd.consultation_fee,
        "status": opd.status.upper() if opd.status else "CONFIRMED",
        "qr_token": opd.qr_token
    }

@router.get("", response_model=List[OPDResponse])
def list_opd_appointments(
    patient_id: Optional[str] = Query(None, description="Filter by Patient ID or User ID"),
    doctor_id: Optional[str] = Query(None, description="Filter by Doctor ID"),
    hospital_id: Optional[str] = Query(None, description="Filter by Hospital ID"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. CONFIRMED, VERIFIED, COMPLETED, CANCELLED)"),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """List appointments filtered by patient, doctor, hospital, or status with strict role-based scoping."""
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to view appointments."
        )

    query = db.query(OPDAppointmentModel)

    # Scoping for authenticated PATIENT
    if current_user.role == "PATIENT":
        pat = db.query(PatientModel).filter(
            (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
        ).first()
        allowed_ids = {current_user.id}
        if pat:
            allowed_ids.add(pat.id)
            if pat.user_id:
                allowed_ids.add(pat.user_id)
        query = query.filter(OPDAppointmentModel.patient_id.in_(list(allowed_ids)))

    # Scoping for authenticated HOSPITAL_STAFF / HOSPITAL_ADMIN
    elif current_user.role in ["HOSPITAL_STAFF", "HOSPITAL_ADMIN"]:
        if current_user.hospital_id:
            if hospital_id and hospital_id != current_user.hospital_id:
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You are only authorized to view appointments for your assigned hospital ({current_user.hospital_id})."
                )
            query = query.filter(OPDAppointmentModel.hospital_id == current_user.hospital_id)
        elif hospital_id and isinstance(hospital_id, str):
            query = query.filter(OPDAppointmentModel.hospital_id == hospital_id)

    # Scoping for authenticated DOCTOR
    elif current_user.role == "DOCTOR":
        valid_doctor_ids = {current_user.id}
        matching_docs = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
        ).all()
        for md in matching_docs:
            valid_doctor_ids.add(md.id)
        if doctor_id and doctor_id not in valid_doctor_ids:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You are only authorized to view your own assigned appointments."
            )
        query = query.filter(OPDAppointmentModel.doctor_id.in_(list(valid_doctor_ids)))

    # Fallback filtering for ADMIN or unconstrained roles
    else:
        if patient_id and isinstance(patient_id, str):
            patient = db.query(PatientModel).filter(
                (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
            ).first()
            if patient:
                query = query.filter(
                    (OPDAppointmentModel.patient_id == patient_id) |
                    (OPDAppointmentModel.patient_id == patient.id) |
                    (OPDAppointmentModel.patient_id == patient.user_id)
                )
            else:
                query = query.filter(OPDAppointmentModel.patient_id == patient_id)

        if doctor_id and isinstance(doctor_id, str):
            query = query.filter(OPDAppointmentModel.doctor_id == doctor_id)

        if hospital_id and isinstance(hospital_id, str):
            query = query.filter(OPDAppointmentModel.hospital_id == hospital_id)

    if status and isinstance(status, str):
        query = query.filter(OPDAppointmentModel.status.ilike(status.strip()))

    appointments = query.order_by(OPDAppointmentModel.created_at.desc()).all()
    return [opd_to_dict(app) for app in appointments]

@router.post("", response_model=OPDResponse)
def create_opd_appointment(
    payload: OPDCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    with SLOT_MUTATION_LOCK:
        db.expire_all()
        hospital = db.query(HospitalModel).filter(HospitalModel.id == payload.hospital_id).first()
        doctor = db.query(DoctorModel).filter(DoctorModel.id == payload.doctor_id).first()
        patient = db.query(PatientModel).filter(
            (PatientModel.id == payload.patient_id) | (PatientModel.user_id == payload.patient_id)
        ).first()

        app_date = (payload.appointment_date or payload.date or "Today (09 Sep 2026)").strip()
        app_time = (payload.appointment_time or payload.time or "11:30 AM").strip()

        slot_lock = f"{payload.doctor_id}#{app_date}#{app_time}"

        # Enforce slot conflict pre-check
        conflict = db.query(OPDAppointmentModel).filter(
            (OPDAppointmentModel.active_slot_lock == slot_lock) |
            (
                (OPDAppointmentModel.doctor_id == payload.doctor_id) &
                (OPDAppointmentModel.appointment_date == app_date) &
                (OPDAppointmentModel.appointment_time == app_time) &
                (OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"]))
            )
        ).first()

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Doctor {doctor.name if doctor else ''} is already booked on {app_date} at {app_time}. Please select a different time slot."
            )

        # Check if doctor has blocked this slot in their schedule
        if doctor:
            from app.routers.doctors import is_slot_blocked_by_doctor
            if is_slot_blocked_by_doctor(doctor, app_date, app_time):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot book appointment: Doctor {doctor.name} has blocked the slot on {app_date} at {app_time}."
                )

        ref_id = generate_ref_id()
        while db.query(OPDAppointmentModel).filter(OPDAppointmentModel.reference_id == ref_id).first():
            ref_id = generate_ref_id()

        token = f"TOKEN_SECURE_{ref_id}_{int(datetime.datetime.utcnow().timestamp()*1000)}"
        opd_id = f"opd-{int(datetime.datetime.utcnow().timestamp()*1000)}"

        opd = OPDAppointmentModel(
            id=opd_id,
            reference_id=ref_id,
            patient_id=payload.patient_id,
            patient_name=patient.full_name if patient else "Ramesh Sharma",
            patient_phone=patient.phone if patient else "+91 98765 43210",
            hospital_id=payload.hospital_id,
            hospital_name=hospital.name if hospital else "CarePlus Super Specialty Hospital",
            department=payload.department,
            doctor_id=payload.doctor_id,
            doctor_name=doctor.name if doctor else "Dr. Rajesh Kulkarni",
            appointment_date=app_date,
            appointment_time=app_time,
            consultation_fee=doctor.consultation_fee if doctor else 800,
            status="CONFIRMED",
            active_slot_lock=slot_lock,
            qr_token=token
        )
        db.add(opd)

        # Automatically create matching QR Reference in the single database source of truth
        qr = QRReferenceModel(
            id=f"qr-{opd_id}",
            reference_id=ref_id,
            token=token,
            patient_id=payload.patient_id,
            hospital_id=payload.hospital_id,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            is_verified=False
        )
        db.add(qr)

        if patient and patient.care_stage < 6:
            patient.care_stage = 6

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slot collision detected: Doctor {doctor.name if doctor else ''} was booked by another patient simultaneously on {app_date} at {app_time}."
            )

        db.refresh(opd)
        return opd_to_dict(opd)

@router.get("/{appointment_id}", response_model=OPDResponse)
def get_opd_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    opd = db.query(OPDAppointmentModel).filter(OPDAppointmentModel.id == appointment_id).first()
    if not opd:
        raise HTTPException(status_code=404, detail="Appointment not found")

    is_authorized = False

    # 1. Patient who booked/owns appointment
    if current_user.role == "PATIENT":
        valid_patient_ids = [current_user.id]
        patient = db.query(PatientModel).filter(PatientModel.user_id == current_user.id).first()
        if patient:
            valid_patient_ids.extend([patient.id, patient.user_id])
        if opd.patient_id in valid_patient_ids:
            is_authorized = True

    # 2. Doctor assigned to appointment or at same hospital
    elif current_user.role == "DOCTOR":
        valid_doctor_ids = {current_user.id}
        matching_docs = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
        ).all()
        for md in matching_docs:
            valid_doctor_ids.add(md.id)
        if opd.doctor_id in valid_doctor_ids or (current_user.name and opd.doctor_name and current_user.name.strip().lower() == opd.doctor_name.strip().lower()):
            is_authorized = True
        elif current_user.hospital_id and current_user.hospital_id == opd.hospital_id:
            is_authorized = True

    # 3. Hospital Admin/Staff for the hospital
    elif current_user.role in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF"]:
        if not current_user.hospital_id or current_user.hospital_id == opd.hospital_id:
            is_authorized = True

    elif current_user.role == "ADMIN":
        is_authorized = True

    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to view this appointment's details."
        )

    return opd_to_dict(opd)

@router.get("/reference/{reference_id}", response_model=OPDResponse)
def get_opd_by_reference(reference_id: str, db: Session = Depends(get_db)):
    clean_ref = reference_id.strip().upper()
    opd = db.query(OPDAppointmentModel).filter(OPDAppointmentModel.reference_id == clean_ref).first()
    if not opd:
        raise HTTPException(status_code=404, detail=f"Appointment with reference ID {clean_ref} not found")
    return opd_to_dict(opd)

@router.put("/{appointment_id}/cancel", response_model=OPDResponse)
def cancel_opd_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Cancel an appointment and invalidate its associated QR token."""
    with SLOT_MUTATION_LOCK:
        db.expire_all()
        opd = db.query(OPDAppointmentModel).filter(OPDAppointmentModel.id == appointment_id).first()
        if not opd:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to cancel an appointment."
            )

        # Authorization guard: if patient is logged in, verify ownership
        if isinstance(current_user, UserModel) and current_user.role == "PATIENT":
            patient = db.query(PatientModel).filter(PatientModel.user_id == current_user.id).first()
            valid_ids = [current_user.id]
            if patient:
                valid_ids.append(patient.id)
            if opd.patient_id not in valid_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You are not authorized to cancel an appointment belonging to another patient."
                )

        if opd.status == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a completed consultation appointment."
            )

        if opd.status == "CANCELLED":
            return opd_to_dict(opd)

        opd.status = "CANCELLED"
        opd.active_slot_lock = None  # Release slot lock so slot becomes bookable again

        # Expire QR token immediately
        qr = db.query(QRReferenceModel).filter(QRReferenceModel.reference_id == opd.reference_id).first()
        if qr:
            qr.expires_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)

        db.commit()
        db.refresh(opd)
        return opd_to_dict(opd)

@router.put("/{appointment_id}/reschedule", response_model=OPDResponse)
def reschedule_opd_appointment(
    appointment_id: str,
    payload: OPDRescheduleRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Reschedule an existing appointment to a new date and time slot."""
    with SLOT_MUTATION_LOCK:
        db.expire_all()
        opd = db.query(OPDAppointmentModel).filter(OPDAppointmentModel.id == appointment_id).first()
        if not opd:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to reschedule an appointment."
            )

        # Authorization guard
        if isinstance(current_user, UserModel) and current_user.role == "PATIENT":
            patient = db.query(PatientModel).filter(PatientModel.user_id == current_user.id).first()
            valid_ids = [current_user.id]
            if patient:
                valid_ids.append(patient.id)
            if opd.patient_id not in valid_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You cannot reschedule another patient's appointment."
                )

        if opd.status == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reschedule a completed consultation appointment."
            )

        if opd.status == "CANCELLED":
            raise HTTPException(status_code=400, detail="Cannot reschedule a cancelled appointment. Please book a new one.")

        new_date = payload.appointment_date.strip()
        new_time = payload.appointment_time.strip()
        new_slot_lock = f"{opd.doctor_id}#{new_date}#{new_time}"

        # Check for conflicts at new date and time
        conflict = db.query(OPDAppointmentModel).filter(
            (OPDAppointmentModel.active_slot_lock == new_slot_lock) |
            (
                (OPDAppointmentModel.doctor_id == opd.doctor_id) &
                (OPDAppointmentModel.appointment_date == new_date) &
                (OPDAppointmentModel.appointment_time == new_time) &
                (OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"]))
            ),
            OPDAppointmentModel.id != appointment_id
        ).first()

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slot {new_date} at {new_time} is already booked for this doctor. Please choose another slot."
            )

        # Check if doctor has blocked this slot in their schedule
        doctor = db.query(DoctorModel).filter(
            (DoctorModel.id == opd.doctor_id) | (DoctorModel.name == opd.doctor_name)
        ).first()
        if doctor:
            from app.routers.doctors import is_slot_blocked_by_doctor
            if is_slot_blocked_by_doctor(doctor, new_date, new_time):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot reschedule: Doctor {doctor.name} has blocked the slot on {new_date} at {new_time}."
                )

        opd.appointment_date = new_date
        opd.appointment_time = new_time
        opd.active_slot_lock = new_slot_lock
        opd.status = "CONFIRMED"

        # Refresh QR expiry
        qr = db.query(QRReferenceModel).filter(QRReferenceModel.reference_id == opd.reference_id).first()
        if qr:
            qr.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            qr.is_verified = False

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slot collision detected: Slot {new_date} at {new_time} was just booked by another patient."
            )

        db.refresh(opd)
        return opd_to_dict(opd)
