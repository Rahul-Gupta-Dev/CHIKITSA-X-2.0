import datetime
from sqlalchemy import Column, String, Boolean, JSON, DateTime
from app.database import Base

class MedicalRecordModel(Base):
    __tablename__ = "medical_records"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # PDF, JPG, PNG
    category = Column(String, nullable=False) # Prescription, Lab Report, Discharge Summary, etc.
    upload_date = Column(String, nullable=False)
    ocr_extracted_data = Column(JSON, nullable=False)
    file_path = Column(String, nullable=True)
    is_verified_by_patient = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
