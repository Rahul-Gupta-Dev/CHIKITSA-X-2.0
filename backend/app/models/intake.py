import datetime
from sqlalchemy import Column, String, Boolean, JSON, DateTime
from app.database import Base

class IntakeSessionModel(Base):
    __tablename__ = "intake_sessions"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_transcript = Column(String, nullable=False)
    extracted_symptoms = Column(JSON, default=list)
    duration = Column(String, default="Recent")
    severity = Column(String, default="Moderate") # Mild, Moderate, Severe, Critical
    affected_body_part = Column(String, nullable=True)
    trigger_event = Column(String, nullable=True)
    is_emergency_alert = Column(Boolean, default=False)
