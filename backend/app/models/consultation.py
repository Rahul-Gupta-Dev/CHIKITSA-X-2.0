import datetime
from sqlalchemy import Column, String, JSON, DateTime
from app.database import Base

class ConsultationModel(Base):
    __tablename__ = "consultations"

    id = Column(String, primary_key=True, index=True)
    appointment_id = Column(String, index=True, nullable=False)
    reference_id = Column(String, nullable=False)
    patient_id = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=False)
    doctor_id = Column(String, index=True, nullable=False)
    doctor_name = Column(String, nullable=False)
    hospital_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    clinical_notes = Column(String, nullable=False)
    diagnosis = Column(String, nullable=False)
    investigations_ordered = Column(JSON, default=list)
    prescription_medicines = Column(JSON, default=list) # [{name, dosage, duration}]
    treatment_plan = Column(String, nullable=False)
    treatment_cost_estimate_id = Column(String, nullable=True)
    status = Column(String, default="COMPLETED")

class ConsultationDraftModel(Base):
    __tablename__ = "consultation_drafts"

    id = Column(String, primary_key=True, index=True)
    appointment_id = Column(String, unique=True, index=True, nullable=False)
    reference_id = Column(String, nullable=False)
    patient_id = Column(String, index=True, nullable=False)
    doctor_id = Column(String, index=True, nullable=False)
    doctor_name = Column(String, nullable=False)
    hospital_id = Column(String, nullable=False)
    clinical_notes = Column(String, nullable=True)
    diagnosis = Column(String, nullable=True)
    investigations_ordered = Column(JSON, default=list)
    prescription_medicines = Column(JSON, default=list) # [{name, dosage, duration}]
    treatment_plan = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
