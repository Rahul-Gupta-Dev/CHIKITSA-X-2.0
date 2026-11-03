import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from app.database import get_db, SLOT_MUTATION_LOCK
from app.auth import get_current_user_optional
from app.models.user import UserModel
from app.models.consultation import ConsultationModel, ConsultationDraftModel
from app.models.opd import OPDAppointmentModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.consent import ConsentLogModel
from app.schemas import ConsultationCreateRequest, ConsultationOut, ConsultationDraftRequest, ConsultationDraftOut

router = APIRouter(prefix="/api/consultations", tags=["Doctor Consultations"])

def consultation_to_dict(c: ConsultationModel) -> Dict[str, Any]:
    return {
        "id": c.id,
        "appointmentId": c.appointment_id,
        "referenceId": c.reference_id,
        "patientId": c.patient_id,
        "patientName": c.patient_name,
        "doctorId": c.doctor_id,
        "doctorName": c.doctor_name,
        "hospitalId": c.hospital_id,
        "clinicalNotes": c.clinical_notes,
        "diagnosis": c.diagnosis,
        "investigationsOrdered": c.investigations_ordered or [],
        "prescriptionMedicines": c.prescription_medicines or [],
        "treatmentPlan": c.treatment_plan,
        "status": c.status
    }

@router.post("", response_model=ConsultationOut)
def record_consultation(
    payload: ConsultationCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    # 1. Require authentication
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to finalize consultation."
        )

    # 2. Only authenticated DOCTOR may finalize consultations
    if current_user.role != "DOCTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only doctors can finalize consultations."
        )

    # 3. Validate appointment_id
    appointment_id = payload.appointment_id or payload.appointmentId
    if not appointment_id or not appointment_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="appointment_id is required."
        )

    opd = db.query(OPDAppointmentModel).filter(OPDAppointmentModel.id == appointment_id.strip()).first()
    if not opd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated OPD Appointment not found."
        )

    # 4. Validate doctor assignment
    valid_doctor_ids = {current_user.id}
    matching_docs = db.query(DoctorModel).filter(
        (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
    ).all()
    for md in matching_docs:
        valid_doctor_ids.add(md.id)

    is_assigned = (opd.doctor_id in valid_doctor_ids)
    if not is_assigned and current_user.name and opd.doctor_name:
        if current_user.name.strip().lower() == opd.doctor_name.strip().lower():
            is_assigned = True

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not the assigned doctor for this appointment."
        )

    # 5. Validate patient ID if supplied
    payload_patient_id = payload.patient_id or payload.patientId
    if payload_patient_id and payload_patient_id.strip():
        payload_pid = payload_patient_id.strip()
        valid_patient_ids = {opd.patient_id}
        pat = db.query(PatientModel).filter(
            (PatientModel.id == opd.patient_id) | (PatientModel.user_id == opd.patient_id)
        ).first()
        if pat:
            valid_patient_ids.add(pat.id)
            if pat.user_id:
                valid_patient_ids.add(pat.user_id)
        if payload_pid not in valid_patient_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conflicting patient ID: provided patient_id does not match the appointment patient."
            )

    with SLOT_MUTATION_LOCK:
        db.expire_all()
        # 6. Prevent duplicate finalization
        existing_cons = db.query(ConsultationModel).filter(ConsultationModel.appointment_id == opd.id).first()
        if existing_cons or (opd.status and opd.status.upper() == "COMPLETED"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Consultation has already been finalized for this appointment."
            )

        # 7. Validate required fields
        clinical_notes = payload.clinical_notes or payload.clinicalNotes
        diagnosis = payload.diagnosis
        treatment_plan = payload.treatment_plan or payload.treatmentPlan

        if not clinical_notes or not clinical_notes.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="clinical_notes is required.")
        if not diagnosis or not diagnosis.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="diagnosis is required.")
        if not treatment_plan or not treatment_plan.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="treatment_plan is required.")

        # 8. Transactional record creation, appointment status update, and care stage advance
        cons_id = f"cons-{int(datetime.datetime.utcnow().timestamp()*1000)}"
        consultation = ConsultationModel(
            id=cons_id,
            appointment_id=opd.id,
            reference_id=opd.reference_id,
            patient_id=opd.patient_id,
            patient_name=opd.patient_name,
            doctor_id=opd.doctor_id,
            doctor_name=opd.doctor_name,
            hospital_id=opd.hospital_id,
            clinical_notes=clinical_notes.strip(),
            diagnosis=diagnosis.strip(),
            investigations_ordered=payload.investigations_ordered or payload.investigationsOrdered or [],
            prescription_medicines=payload.prescription_medicines or payload.prescriptionMedicines or [],
            treatment_plan=treatment_plan.strip(),
            status="COMPLETED"
        )
        db.add(consultation)

        opd.status = "COMPLETED"

        # Clean up draft if one existed for this appointment
        existing_draft = db.query(ConsultationDraftModel).filter(ConsultationDraftModel.appointment_id == opd.id).first()
        if existing_draft:
            db.delete(existing_draft)

        patient = db.query(PatientModel).filter(
            (PatientModel.id == opd.patient_id) | (PatientModel.user_id == opd.patient_id)
        ).first()
        if patient and (patient.care_stage is None or patient.care_stage < 8):
            patient.care_stage = 8

        try:
            db.commit()
            db.refresh(consultation)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Consultation has already been finalized for this appointment."
            )
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database commit error: {str(exc)}"
            )

    return consultation_to_dict(consultation)

@router.post("/draft", response_model=ConsultationDraftOut)
def save_consultation_draft(
    payload: ConsultationDraftRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to save consultation draft."
        )

    if current_user.role != "DOCTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only doctors can save consultation drafts."
        )

    appointment_id = payload.appointment_id or payload.appointmentId
    if not appointment_id or not appointment_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="appointment_id is required."
        )

    opd = db.query(OPDAppointmentModel).filter(OPDAppointmentModel.id == appointment_id.strip()).first()
    if not opd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated OPD Appointment not found."
        )

    # Check assignment
    valid_doctor_ids = {current_user.id}
    matching_docs = db.query(DoctorModel).filter(
        (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
    ).all()
    for md in matching_docs:
        valid_doctor_ids.add(md.id)

    is_assigned = (opd.doctor_id in valid_doctor_ids)
    if not is_assigned and current_user.name and opd.doctor_name:
        if current_user.name.strip().lower() == opd.doctor_name.strip().lower():
            is_assigned = True

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not the assigned doctor for this appointment."
        )

    # Prevent saving draft if already finalized
    existing_cons = db.query(ConsultationModel).filter(ConsultationModel.appointment_id == opd.id).first()
    if existing_cons or (opd.status and opd.status.upper() == "COMPLETED"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot save draft: Consultation has already been finalized for this appointment."
        )

    clinical_notes = payload.clinical_notes or payload.clinicalNotes or ""
    diagnosis = payload.diagnosis or ""
    treatment_plan = payload.treatment_plan or payload.treatmentPlan or ""
    investigations = payload.investigations_ordered or payload.investigationsOrdered or []
    prescriptions = payload.prescription_medicines or payload.prescriptionMedicines or []

    draft = db.query(ConsultationDraftModel).filter(ConsultationDraftModel.appointment_id == opd.id).first()
    if not draft:
        draft = ConsultationDraftModel(
            id=f"draft-{opd.id}",
            appointment_id=opd.id,
            reference_id=opd.reference_id,
            patient_id=opd.patient_id,
            doctor_id=current_user.id,
            doctor_name=current_user.name,
            hospital_id=opd.hospital_id,
            clinical_notes=clinical_notes,
            diagnosis=diagnosis,
            investigations_ordered=investigations,
            prescription_medicines=prescriptions,
            treatment_plan=treatment_plan
        )
        db.add(draft)
    else:
        draft.clinical_notes = clinical_notes
        draft.diagnosis = diagnosis
        draft.treatment_plan = treatment_plan
        draft.investigations_ordered = investigations
        draft.prescription_medicines = prescriptions
        draft.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(draft)

    return {
        "id": draft.id,
        "appointmentId": draft.appointment_id,
        "referenceId": draft.reference_id,
        "patientId": draft.patient_id,
        "doctorId": draft.doctor_id,
        "doctorName": draft.doctor_name,
        "hospitalId": draft.hospital_id,
        "clinicalNotes": draft.clinical_notes,
        "diagnosis": draft.diagnosis,
        "investigationsOrdered": draft.investigations_ordered or [],
        "prescriptionMedicines": draft.prescription_medicines or [],
        "treatmentPlan": draft.treatment_plan,
        "updatedAt": draft.updated_at.isoformat() if draft.updated_at else datetime.datetime.utcnow().isoformat()
    }

@router.get("/draft/{appointment_id}", response_model=ConsultationDraftOut)
def get_consultation_draft(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view consultation draft."
        )

    if current_user.role != "DOCTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only doctors can view consultation drafts."
        )

    draft = db.query(ConsultationDraftModel).filter(
        (ConsultationDraftModel.appointment_id == appointment_id) | (ConsultationDraftModel.id == appointment_id)
    ).first()

    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation draft not found.")

    # Doctor assignment check
    valid_doctor_ids = {current_user.id}
    matching_docs = db.query(DoctorModel).filter(
        (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
    ).all()
    for md in matching_docs:
        valid_doctor_ids.add(md.id)

    is_assigned = (draft.doctor_id in valid_doctor_ids)
    if not is_assigned and current_user.name and draft.doctor_name:
        if current_user.name.strip().lower() == draft.doctor_name.strip().lower():
            is_assigned = True

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to view another doctor's consultation draft."
        )

    return {
        "id": draft.id,
        "appointmentId": draft.appointment_id,
        "referenceId": draft.reference_id,
        "patientId": draft.patient_id,
        "doctorId": draft.doctor_id,
        "doctorName": draft.doctor_name,
        "hospitalId": draft.hospital_id,
        "clinicalNotes": draft.clinical_notes,
        "diagnosis": draft.diagnosis,
        "investigationsOrdered": draft.investigations_ordered or [],
        "prescriptionMedicines": draft.prescription_medicines or [],
        "treatmentPlan": draft.treatment_plan,
        "updatedAt": draft.updated_at.isoformat() if draft.updated_at else datetime.datetime.utcnow().isoformat()
    }

@router.get("/{appointment_id}", response_model=ConsultationOut)
def get_consultation(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view consultation."
        )

    cons = db.query(ConsultationModel).filter(
        (ConsultationModel.appointment_id == appointment_id) | (ConsultationModel.id == appointment_id)
    ).first()
    if not cons:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation record not found")

    # Access control
    if current_user.role == "PATIENT":
        valid_patient_ids = {current_user.id}
        pat = db.query(PatientModel).filter(
            (PatientModel.id == current_user.id) | (PatientModel.user_id == current_user.id)
        ).first()
        if pat:
            valid_patient_ids.add(pat.id)
            if pat.user_id:
                valid_patient_ids.add(pat.user_id)
        if cons.patient_id not in valid_patient_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access consultation records of another patient."
            )

    elif current_user.role == "DOCTOR":
        valid_doctor_ids = {current_user.id}
        matching_docs = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
        ).all()
        for md in matching_docs:
            valid_doctor_ids.add(md.id)

        is_assigned = (cons.doctor_id in valid_doctor_ids)
        if not is_assigned and current_user.name and cons.doctor_name:
            if current_user.name.strip().lower() == cons.doctor_name.strip().lower():
                is_assigned = True

        if not is_assigned:
            has_consent = db.query(ConsentLogModel).filter(
                (ConsentLogModel.patient_id == cons.patient_id),
                (ConsentLogModel.doctor_id.in_(list(valid_doctor_ids)) | (ConsentLogModel.doctor_name == current_user.name)),
                (ConsentLogModel.status == "GRANTED")
            ).first()
            if not has_consent:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Doctor is not assigned to this consultation and lacks active patient consent."
                )

    elif current_user.role in ["HOSPITAL_STAFF", "HOSPITAL_ADMIN"]:
        if current_user.hospital_id and cons.hospital_id and current_user.hospital_id != cons.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Hospital staff cannot view consultations of other hospitals."
            )

    return consultation_to_dict(cons)
