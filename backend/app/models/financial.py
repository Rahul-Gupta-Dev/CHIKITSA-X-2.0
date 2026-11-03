import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime
from app.database import Base

class InsurancePolicyModel(Base):
    __tablename__ = "insurance_policies"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    provider_name = Column(String, nullable=False)
    policy_number = Column(String, nullable=False)
    sum_insured = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    co_pay_percentage = Column(Float, default=0.0)
    is_cashless_available = Column(Boolean, default=True)
    status = Column(String, default="ACTIVE")

class InsuranceClaimModel(Base):
    __tablename__ = "insurance_claims"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    policy_id = Column(String, nullable=False)
    treatment_cost_estimate_id = Column(String, nullable=False)
    claimed_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, nullable=True)
    status = Column(String, default="SUBMITTED")
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    claim_reference_number = Column(String, nullable=False)

class GovernmentSchemeModel(Base):
    __tablename__ = "government_schemes"

    id = Column(String, primary_key=True, index=True)
    scheme_code = Column(String, unique=True, nullable=False)
    scheme_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    max_benefit_amount = Column(Float, nullable=False)
    eligibility_criteria = Column(JSON, nullable=False)
    required_documents = Column(JSON, default=list)
    contact_helpline = Column(String, nullable=False)

class NGOSupportModel(Base):
    __tablename__ = "ngo_support"

    id = Column(String, primary_key=True, index=True)
    organization_name = Column(String, nullable=False)
    support_type = Column(String, nullable=False)
    max_assistance_amount = Column(Float, nullable=False)
    eligibility_description = Column(String, nullable=False)
    required_documents = Column(JSON, default=list)
    application_status = Column(String, default="AVAILABLE")

class CareToCostAssessmentModel(Base):
    __tablename__ = "care_to_cost_assessments"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True, nullable=False)
    hospital_name = Column(String, nullable=False)
    estimated_treatment_cost = Column(Float, nullable=False)
    insurance_coverage = Column(Float, default=0.0)
    government_support = Column(Float, default=0.0)
    ngo_assistance = Column(Float, default=0.0)
    patient_self_contribution = Column(Float, default=0.0)
    financial_gap = Column(Float, default=0.0)
    is_funding_complete = Column(Boolean, default=False)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow)

class TreatmentCostEstimateModel(Base):
    __tablename__ = "treatment_cost_estimates"

    id = Column(String, primary_key=True, index=True)
    consultation_id = Column(String, nullable=True)
    patient_id = Column(String, index=True, nullable=False)
    hospital_id = Column(String, nullable=False)
    hospital_name = Column(String, nullable=False)
    procedure_name = Column(String, nullable=False)
    room_category = Column(String, nullable=False)
    estimated_cost_range = Column(JSON, nullable=False)
    breakdown = Column(JSON, nullable=False)
    confidence_level = Column(String, default="INDICATIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
