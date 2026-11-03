import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.database import Base

class QRReferenceModel(Base):
    __tablename__ = "qr_references"

    id = Column(String, primary_key=True, index=True)
    reference_id = Column(String, unique=True, index=True, nullable=False)
    token = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by_staff = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
