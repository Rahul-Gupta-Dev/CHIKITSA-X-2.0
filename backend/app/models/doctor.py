import datetime
from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey
from app.database import Base

class DoctorModel(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, index=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False)
    hospital_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    qualification = Column(String, nullable=False)
    experience_years = Column(Integer, default=5)
    rating = Column(Float, default=4.5)
    consultation_fee = Column(Integer, default=500)
    available_days = Column(JSON, default=list)
    available_slots = Column(JSON, default=list)
    weekly_schedule = Column(JSON, default=list)
    blocked_slots = Column(JSON, default=list)
    avatar = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
