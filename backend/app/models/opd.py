import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database import Base

class OPDAppointmentModel(Base):
    __tablename__ = "opd_appointments"

    id = Column(String, primary_key=True, index=True)
    reference_id = Column(String, unique=True, index=True, nullable=False) # e.g. CHX-2026-8A92F
    patient_id = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    patient_phone = Column(String, nullable=False)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False)
    hospital_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False)
    consultation_fee = Column(Integer, default=500)
    status = Column(String, default="CONFIRMED") # CONFIRMED, VERIFIED, COMPLETED, CANCELLED
    active_slot_lock = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    qr_token = Column(String, nullable=False)
