import datetime
from sqlalchemy import Column, String, Boolean, JSON, DateTime
from app.database import Base

class TriageResultModel(Base):
    __tablename__ = "triage_results"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    risk_level = Column(String, nullable=False) # LOW, MODERATE, HIGH
    urgency = Column(String, nullable=False)
    symptoms_considered = Column(JSON, default=list)
    clinical_reasoning = Column(JSON, default=list)
    recommended_specialty = Column(String, nullable=False)
    recommended_next_step = Column(String, nullable=False)
    is_emergency_triggered = Column(Boolean, default=False)
