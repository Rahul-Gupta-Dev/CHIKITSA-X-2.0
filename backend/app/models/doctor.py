import datetime
from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey
from app.database import Base

class DoctorModel(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), unique=True, index=True, nullable=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False)
    hospital_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    qualification = Column(String, nullable=False)
    medical_registration_number = Column(String(64), nullable=True)
    verification_status = Column(String(32), default="VERIFIED", nullable=True)
    experience_years = Column(Integer, default=5)
    rating = Column(Float, default=4.5)
    consultation_fee = Column(Integer, default=500)
    available_days = Column(JSON, default=list)
    available_slots = Column(JSON, default=list)
    weekly_schedule = Column(JSON, default=list)
    blocked_slots = Column(JSON, default=list)
    avatar = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
