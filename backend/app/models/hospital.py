import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime
from app.database import Base

class HospitalModel(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    tagline = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    distance_km = Column(Float, default=0.0)
    phone = Column(String, nullable=False)
    emergency_phone = Column(String, nullable=False)
    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=0)
    emergency_available = Column(Boolean, default=True)
    emergency_beds_free = Column(Integer, default=0)
    icu_beds_free = Column(Integer, default=0)
    specialties = Column(JSON, default=list)
    clinical_fit_score = Column(Float, default=80.0)
    affordability_score = Column(Float, default=80.0)
    availability_score = Column(Float, default=80.0)
    support_services_score = Column(Float, default=80.0)
    chikitsax_care_score = Column(Float, default=80.0)
    estimated_cost_range = Column(JSON, nullable=False) # {min, max}
    accepted_insurance_providers = Column(JSON, default=list)
    accepted_gov_schemes = Column(JSON, default=list)
    ngo_partnerships = Column(JSON, default=list)
    accreditation = Column(JSON, default=list)
    opd_slot_availability = Column(String, default="HIGH")
    image = Column(String, nullable=True)
    why_recommended = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class HospitalReviewModel(Base):
    __tablename__ = "hospital_reviews"

    id = Column(String, primary_key=True, index=True)
    hospital_id = Column(String, index=True, nullable=False)
    patient_id = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=False)
    rating = Column(Float, nullable=False)
    review_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
