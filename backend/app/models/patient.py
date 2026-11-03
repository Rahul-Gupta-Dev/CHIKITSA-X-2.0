import datetime
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, ForeignKey
from app.database import Base

class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    emergency_contact = Column(JSON, nullable=True) # {name, relationship, phone}
    symptoms = Column(JSON, default=list)
    medical_history = Column(JSON, default=list)
    medications = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    vital_signs = Column(JSON, nullable=True) # {bp, pulse, spo2, temp}
    care_stage = Column(Integer, default=1)
    financial_budget_preference = Column(String, default="MEDIUM")
    has_insurance = Column(Boolean, default=False)
    insurance_provider = Column(String, nullable=True)
    policy_number = Column(String, nullable=True)
    has_government_card = Column(Boolean, default=False)
    ration_card_type = Column(String, nullable=True)
    income_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
