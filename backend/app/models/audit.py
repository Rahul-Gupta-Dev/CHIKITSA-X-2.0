import datetime
from sqlalchemy import Column, String, DateTime
from app.database import Base

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    actor_role = Column(String, nullable=False) # PATIENT, DOCTOR, HOSPITAL_ADMIN
    actor_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
