import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.auth import get_current_user, get_current_user_optional
from app.models.user import UserModel
from app.models.consent import ConsentLogModel
from app.models.medical_record import MedicalRecordModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.schemas import MedicalRecordCreate, MedicalRecordOut
from app.services.ocr_service import OCRService

router = APIRouter(prefix="/api/medical-records", tags=["Medical Records"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "medical_records")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".txt"}

@router.post("", response_model=MedicalRecordOut)
def upload_medical_record(
    payload: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Authorization checks
    curr_patient = db.query(PatientModel).filter(
        (PatientModel.user_id == current_user.id) | (PatientModel.id == current_user.id)
    ).first()

    if current_user.role == "PATIENT":
        valid_ids = [current_user.id]
        if curr_patient:
            valid_ids.extend([curr_patient.id, curr_patient.user_id])
        if payload.patient_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Patients can only create medical records for themselves."
            )
    elif current_user.role == "DOCTOR":
        p_ids = [payload.patient_id]
        target_patient = db.query(PatientModel).filter(
            (PatientModel.id == payload.patient_id) | (PatientModel.user_id == payload.patient_id)
        ).first()
        if target_patient:
            p_ids.extend([target_patient.id, target_patient.user_id])

        valid_doctor_ids = {current_user.id}
        matching_docs = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
        ).all()
        for md in matching_docs:
            valid_doctor_ids.add(md.id)

        has_consent = db.query(ConsentLogModel).filter(
            ConsentLogModel.patient_id.in_(p_ids),
            ConsentLogModel.status == "GRANTED"
        ).first()

        has_appointment = db.query(OPDAppointmentModel).filter(
            OPDAppointmentModel.patient_id.in_(p_ids),
            OPDAppointmentModel.doctor_id.in_(valid_doctor_ids)
        ).first()

        if not (has_consent or has_appointment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctors can only create records for patients with active consent or an assigned appointment."
            )
    elif current_user.role not in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Unauthorized role for creating medical records."
        )

    if payload.ocr_extracted_data:
        extracted = payload.ocr_extracted_data
    else:
        raw_text = payload.raw_text or f"Sample extracted medical record for {payload.file_name}"
        extracted = OCRService.extract_medical_fields(raw_text, payload.category, payload.file_name)

    rec_id = f"ocr-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    today_str = datetime.datetime.utcnow().strftime("%d %b %Y")

    record = MedicalRecordModel(
        id=rec_id,
        patient_id=payload.patient_id,
        file_name=payload.file_name,
        file_type=payload.file_type.upper(),
        category=payload.category,
        upload_date=today_str,
        ocr_extracted_data=extracted,
        is_verified_by_patient=True
    )
    db.add(record)

    # Sync medications and allergies to patient profile
    patient = db.query(PatientModel).filter(
        (PatientModel.id == payload.patient_id) | (PatientModel.user_id == payload.patient_id)
    ).first()
    if patient:
        new_meds = extracted.get("medicinesExtracted", [])
        new_allergies = extracted.get("allergiesExtracted", [])
        merged_meds = list(dict.fromkeys((patient.medications or []) + new_meds))
        merged_allergies = list(dict.fromkeys((patient.allergies or []) + new_allergies))
        patient.medications = merged_meds
        patient.allergies = merged_allergies
        if patient.care_stage < 3:
            patient.care_stage = 3

    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "patient_id": record.patient_id,
        "file_name": record.file_name,
        "file_type": record.file_type,
        "category": record.category,
        "upload_date": record.upload_date,
        "ocr_extracted_data": record.ocr_extracted_data,
        "is_verified_by_patient": record.is_verified_by_patient
    }

@router.post("/upload")
async def upload_file_multipart(
    patient_id: str = Form("usr-patient-1"),
    category: str = Form("Prescription"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role == "PATIENT":
        patient_id = current_user.id
    elif current_user.role == "DOCTOR":
        p_ids = [patient_id]
        target_patient = db.query(PatientModel).filter(
            (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
        ).first()
        if target_patient:
            p_ids.extend([target_patient.id, target_patient.user_id])

        valid_doctor_ids = {current_user.id}
        matching_docs = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
        ).all()
        for md in matching_docs:
            valid_doctor_ids.add(md.id)

        has_consent = db.query(ConsentLogModel).filter(
            ConsentLogModel.patient_id.in_(p_ids),
            ConsentLogModel.status == "GRANTED"
        ).first()

        has_appointment = db.query(OPDAppointmentModel).filter(
            OPDAppointmentModel.patient_id.in_(p_ids),
            OPDAppointmentModel.doctor_id.in_(valid_doctor_ids)
        ).first()

        if not (has_consent or has_appointment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctors can only upload records for patients with active consent or an assigned appointment."
            )

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    clean_filename = os.path.basename(file.filename)
    if ".." in clean_filename or "/" in clean_filename or "\\" in clean_filename:
        raise HTTPException(status_code=400, detail="Invalid or unsafe filename.")

    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{ext}'. Supported formats: PDF, JPG, JPEG, PNG."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty or corrupt file uploaded")
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 15MB limit")

    file_type = ext.replace(".", "").upper()
    if file_type == "JPEG":
        file_type = "JPG"

    raw_text = OCRService.extract_text(content, file.filename, category)
    extracted = OCRService.extract_medical_fields(raw_text, category, file.filename)

    rec_id = f"ocr-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    today_str = datetime.datetime.utcnow().strftime("%d %b %Y")

    # Persist file securely to disk
    file_save_path = os.path.join(UPLOAD_DIR, f"{rec_id}_{file.filename}")
    try:
        with open(file_save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        file_save_path = None

    record = MedicalRecordModel(
        id=rec_id,
        patient_id=patient_id,
        file_name=file.filename,
        file_type=file_type,
        category=category,
        upload_date=today_str,
        ocr_extracted_data=extracted,
        file_path=file_save_path,
        is_verified_by_patient=True
    )
    db.add(record)

    patient = db.query(PatientModel).filter(
        (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
    ).first()
    if patient:
        new_meds = extracted.get("medicinesExtracted", [])
        new_allergies = extracted.get("allergiesExtracted", [])
        merged_meds = list(dict.fromkeys((patient.medications or []) + new_meds))
        merged_allergies = list(dict.fromkeys((patient.allergies or []) + new_allergies))
        patient.medications = merged_meds
        patient.allergies = merged_allergies
        if patient.care_stage < 3:
            patient.care_stage = 3

    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "record_id": record.id,
        "patient_id": record.patient_id,
        "file_name": record.file_name,
        "file_type": record.file_type,
        "category": record.category,
        "upload_date": record.upload_date,
        "extraction_status": "development_mock_adapter",
        "extracted_fields": record.ocr_extracted_data,
        "ocr_extracted_data": record.ocr_extracted_data,
        "is_verified_by_patient": record.is_verified_by_patient
    }

@router.get("/{patient_id}", response_model=List[MedicalRecordOut])
def get_records_by_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view medical records."
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
            # Patient can only read their own records
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
            # Doctor must have active granted consent from this patient
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
                    detail="Forbidden: Active patient consent is required to access medical records. Consent is either revoked, pending, or not requested."
                )

    records = db.query(MedicalRecordModel).filter(
        (MedicalRecordModel.patient_id == patient_id) |
        (MedicalRecordModel.patient_id == (patient.id if patient else "")) |
        (MedicalRecordModel.patient_id == (patient.user_id if patient else ""))
    ).order_by(MedicalRecordModel.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "category": r.category,
            "upload_date": r.upload_date,
            "ocr_extracted_data": r.ocr_extracted_data,
            "is_verified_by_patient": r.is_verified_by_patient
        }
        for r in records
    ]

@router.get("/file/{record_id}")
def download_record_file(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Download or view stored medical record document file."""
    record = db.query(MedicalRecordModel).filter(MedicalRecordModel.id == record_id).first()
    if not record or not record.file_path or not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="Medical record document file not found")

    # Safe path traversal check
    real_path = os.path.realpath(record.file_path)
    real_upload_dir = os.path.realpath(UPLOAD_DIR)
    if not real_path.startswith(real_upload_dir):
        raise HTTPException(status_code=403, detail="Illegal file path access blocked.")

    # Authorization check
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to download medical record document."
        )

    if isinstance(current_user, UserModel):
        curr_patient = db.query(PatientModel).filter(
            (PatientModel.id == current_user.id) | (PatientModel.user_id == current_user.id)
        ).first()

        rec_patient = db.query(PatientModel).filter(
            (PatientModel.id == record.patient_id) | (PatientModel.user_id == record.patient_id)
        ).first()

        if current_user.role == "PATIENT":
            valid_ids = [current_user.id]
            if curr_patient:
                valid_ids.append(curr_patient.id)
                if curr_patient.user_id:
                    valid_ids.append(curr_patient.user_id)
            if record.patient_id not in valid_ids:
                raise HTTPException(status_code=403, detail="Forbidden: Cannot download medical records of another patient.")
        elif current_user.role == "DOCTOR":
            p_ids = [record.patient_id]
            if rec_patient:
                p_ids.extend([rec_patient.id, rec_patient.user_id])
            consent = db.query(ConsentLogModel).filter(
                ConsentLogModel.patient_id.in_(p_ids),
                ConsentLogModel.status == "GRANTED"
            ).first()
            if not consent:
                raise HTTPException(status_code=403, detail="Forbidden: Active clinical consent required to download patient file.")

    return FileResponse(record.file_path, filename=record.file_name)
