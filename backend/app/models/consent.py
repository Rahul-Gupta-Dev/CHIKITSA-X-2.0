import datetime
from sqlalchemy import Column, String, JSON, DateTime
from app.database import Base

class ConsentLogModel(Base):
    __tablename__ = "consent_logs"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    hospital_id = Column(String, nullable=False)
    hospital_name = Column(String, nullable=False)
    doctor_id = Column(String, nullable=True)
    doctor_name = Column(String, nullable=True)
    requested_at = Column(DateTime, default=datetime.datetime.utcnow)
    granted_at = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING") # PENDING, GRANTED, REVOKED
    accessible_sections = Column(JSON, default=list)
