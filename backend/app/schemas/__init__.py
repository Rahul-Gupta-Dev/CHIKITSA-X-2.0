from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Health Schema
class HealthResponse(BaseModel):
    status: str
    service: str

# User Schemas
class UserBase(BaseModel):
    email: str
    name: str
    role: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    hospitalId: Optional[str] = None

class UserCreate(UserBase):
    id: Optional[str] = None

class UserOut(UserBase):
    id: str

class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = None

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    fullName: Optional[str] = None
    role: str = "PATIENT"
    phone: Optional[str] = None
    age: Optional[int] = 30
    gender: Optional[str] = "Other"
    bloodGroup: Optional[str] = "B+"
    city: Optional[str] = "New Delhi"
    hospitalId: Optional[str] = None

class AuthTokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: UserOut

# Emergency Contact Schema
class EmergencyContact(BaseModel):
    name: str
    relationship: str
    phone: str

# Patient Schemas
class PatientProfileBase(BaseModel):
    userId: str
    fullName: str
    age: int
    gender: str
    bloodGroup: str
    phone: str
    email: str
    address: str
    city: str
    pincode: str
    emergencyContact: Optional[EmergencyContact] = None
    symptoms: List[str] = []
    medicalHistory: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []
    vitalSigns: Optional[Dict[str, str]] = None
    careStage: int = 1
    financialBudgetPreference: str = "MEDIUM"
    hasInsurance: bool = False
    insuranceProvider: Optional[str] = None
    policyNumber: Optional[str] = None
    hasGovernmentCard: bool = False
    rationCardType: Optional[str] = None
    incomeCategory: Optional[str] = None

class PatientProfileCreate(PatientProfileBase):
    id: Optional[str] = None

class PatientProfileUpdate(BaseModel):
    fullName: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    bloodGroup: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    emergencyContact: Optional[Dict[str, Any]] = None
    symptoms: Optional[List[str]] = None
    medicalHistory: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    careStage: Optional[int] = None
    hasInsurance: Optional[bool] = None
    insuranceProvider: Optional[str] = None
    policyNumber: Optional[str] = None
    hasGovernmentCard: Optional[bool] = None
    rationCardType: Optional[str] = None
    incomeCategory: Optional[str] = None

class PatientProfileOut(PatientProfileBase):
    id: str

# Intake Schemas
class IntakeRequest(BaseModel):
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    transcript: Optional[str] = None
    raw_transcript: Optional[str] = None
    rawTranscript: Optional[str] = None
    language: Optional[str] = "en"
    duration: Optional[str] = "Recent"
    severity: Optional[str] = "Moderate"
    affected_body_part: Optional[str] = None
    affectedBodyPart: Optional[str] = None
    trigger_event: Optional[str] = None
    triggerEvent: Optional[str] = None

class IntakeResponse(BaseModel):
    id: str
    patient_id: str
    patientId: Optional[str] = None
    timestamp: Optional[str] = None
    raw_transcript: str
    rawTranscript: Optional[str] = None
    extracted_symptoms: List[str]
    extractedSymptoms: Optional[List[str]] = None
    duration: str
    severity: str
    affected_body_part: Optional[str] = None
    affectedBodyPart: Optional[str] = None
    trigger_event: Optional[str] = None
    triggerEvent: Optional[str] = None
    is_emergency_alert: bool
    isEmergencyAlert: Optional[bool] = None
    disclaimer: Optional[str] = "AI-assisted symptom extraction only. Clinical evaluation by a licensed physician is required."

# Medical Record Schemas
class MedicalRecordCreate(BaseModel):
    patient_id: str
    file_name: str
    file_type: str
    category: str
    raw_text: Optional[str] = None
    ocr_extracted_data: Optional[Dict[str, Any]] = None

class MedicalRecordOut(BaseModel):
    id: str
    patient_id: str
    file_name: str
    file_type: str
    category: str
    upload_date: str
    ocr_extracted_data: Dict[str, Any]
    is_verified_by_patient: bool

# Triage Schemas
class TriageRequest(BaseModel):
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    intake_id: Optional[str] = None
    intakeId: Optional[str] = None

class TriageResponse(BaseModel):
    id: str
    patient_id: str
    patientId: Optional[str] = None
    timestamp: Optional[str] = None
    risk_level: str
    riskLevel: Optional[str] = None
    urgency: str
    recommended_specialties: Optional[List[str]] = None
    recommended_specialty: Optional[str] = None
    recommendedSpecialty: Optional[str] = None
    symptoms_considered: List[str]
    symptomsConsidered: Optional[List[str]] = None
    reasoning: Optional[List[str]] = None
    clinical_reasoning: Optional[List[str]] = None
    clinicalReasoning: Optional[List[str]] = None
    next_action: Optional[str] = None
    recommended_next_step: Optional[str] = None
    recommendedNextStep: Optional[str] = None
    is_emergency_triggered: bool
    isEmergencyTriggered: Optional[bool] = None
    disclaimer: str = "AI-assisted triage decision support only. Professional medical evaluation by a licensed physician is required."

# Hospital Schemas
class HospitalOut(BaseModel):
    id: str
    name: str
    code: str
    tagline: str
    address: str
    city: str
    distanceKm: float
    phone: str
    emergencyPhone: str
    rating: float
    reviewCount: int
    emergencyAvailable: bool
    emergencyBedsFree: int
    icuBedsFree: int
    specialties: List[str]
    clinicalFitScore: float
    affordabilityScore: float
    availabilityScore: float
    supportServicesScore: float
    chikitsaxCareScore: float
    estimatedCostRange: Dict[str, int]
    acceptedInsuranceProviders: List[str]
    acceptedGovSchemes: List[str]
    ngoPartnerships: List[str]
    accreditation: List[str]
    opdSlotAvailability: str
    image: Optional[str] = None
    whyRecommended: Optional[Dict[str, str]] = None

class HospitalRecommendRequest(BaseModel):
    patient_id: str
    specialty: Optional[str] = None
    budget_preference: Optional[str] = "MEDIUM"
    max_distance_km: Optional[float] = 15.0

class HospitalRecommendationResponse(BaseModel):
    hospitals: List[Dict[str, Any]]

class HospitalReviewCreateRequest(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0)
    review_text: str = Field(..., min_length=2)

class HospitalReviewOut(BaseModel):
    id: str
    hospitalId: str
    patientId: str
    patientName: str
    rating: float
    reviewText: str
    createdAt: str

# Doctor Schemas
class DoctorOut(BaseModel):
    id: str
    hospitalId: str
    hospitalName: str
    name: str
    specialty: str
    qualification: str
    experienceYears: int
    rating: float
    consultationFee: int
    availableDays: List[str]
    availableSlots: List[str]
    weeklySchedule: Optional[List[Dict[str, Any]]] = None
    blockedSlots: Optional[List[Any]] = None
    avatar: Optional[str] = None

class DoctorScheduleItem(BaseModel):
    day: str
    time: str
    slots: Optional[int] = 12
    isBlocked: Optional[bool] = False
    is_blocked: Optional[bool] = None

class DoctorScheduleUpdate(BaseModel):
    weekly_schedule: Optional[List[Dict[str, Any]]] = None
    weeklySchedule: Optional[List[Dict[str, Any]]] = None
    blocked_slots: Optional[List[Any]] = None
    blockedSlots: Optional[List[Any]] = None
    available_days: Optional[List[str]] = None
    availableDays: Optional[List[str]] = None
    available_slots: Optional[List[str]] = None
    availableSlots: Optional[List[str]] = None

class BlockSlotRequest(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    day: Optional[str] = None
    slot: Optional[str] = None
    reason: Optional[str] = "Unavailable / Clinical Duties"
    is_blocked: Optional[bool] = True
    isBlocked: Optional[bool] = True

class DoctorScheduleResponse(BaseModel):
    doctor_id: str
    doctorId: Optional[str] = None
    doctor_name: str
    doctorName: Optional[str] = None
    hospital_id: str
    hospitalId: Optional[str] = None
    hospital_name: Optional[str] = None
    hospitalName: Optional[str] = None
    weekly_schedule: List[Dict[str, Any]]
    weeklySchedule: Optional[List[Dict[str, Any]]] = None
    blocked_slots: List[Any]
    blockedSlots: Optional[List[Any]] = None
    available_days: List[str]
    availableDays: Optional[List[str]] = None
    available_slots: List[str]
    availableSlots: Optional[List[str]] = None

class SlotAvailabilityItem(BaseModel):
    time: str
    is_available: bool
    isAvailable: bool
    is_blocked: bool
    isBlocked: bool
    is_booked: bool
    isBooked: bool

class DoctorAvailabilityResponse(BaseModel):
    doctor_id: str
    doctorId: Optional[str] = None
    date: str
    day: Optional[str] = None
    is_day_blocked: bool
    isDayBlocked: Optional[bool] = None
    slots: List[Dict[str, Any]]

# OPD Registration Schemas
class OPDCreateRequest(BaseModel):
    patient_id: str
    hospital_id: str
    doctor_id: str
    department: str
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None

class OPDRescheduleRequest(BaseModel):
    appointment_date: str
    appointment_time: str

class OPDResponse(BaseModel):
    id: str
    appointment_id: Optional[str] = None
    reference_id: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    hospital_id: str
    hospital_name: Optional[str] = None
    hospital: Optional[str] = None
    department: str
    doctor_id: str
    doctor_name: Optional[str] = None
    doctor: Optional[str] = None
    appointment_date: str
    appointment_time: str
    consultation_fee: Optional[int] = 800
    status: str
    qr_token: Optional[str] = None

# QR Verification Schemas
class QRGenerateRequest(BaseModel):
    appointment_id: str

class QRGenerateResponse(BaseModel):
    reference_id: str
    secure_token: str
    qr_payload: str
    id: Optional[str] = None
    expires_at: Optional[str] = None

class QRVerifyResponse(BaseModel):
    verified: bool
    message: Optional[str] = None
    reference_id: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    doctor: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    status: Optional[str] = None
    appointment: Optional[Dict[str, Any]] = None

class HospitalVerifyRequest(BaseModel):
    reference_id: str
    staff_name: Optional[str] = "Reception Desk Staff"
    hospital_id: Optional[str] = None

# Consent Schemas
class ConsentCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    hospital_id: Optional[str] = None
    hospitalId: Optional[str] = None
    hospital_name: Optional[str] = None
    hospitalName: Optional[str] = None
    doctor_id: Optional[str] = None
    doctorId: Optional[str] = None
    doctor_name: Optional[str] = None
    doctorName: Optional[str] = None
    consent_type: Optional[str] = "MEDICAL_RECORD_SHARING"
    granted: bool = True

class ConsentOut(BaseModel):
    id: str
    patientId: str
    hospitalId: str
    hospitalName: str
    doctorId: Optional[str] = None
    doctorName: Optional[str] = None
    status: str
    accessibleSections: List[str]

# Consultation Schemas
class ConsultationCreateRequest(BaseModel):
    appointment_id: Optional[str] = None
    appointmentId: Optional[str] = None
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    clinical_notes: Optional[str] = None
    clinicalNotes: Optional[str] = None
    diagnosis: Optional[str] = None
    investigations_ordered: Optional[List[str]] = None
    investigationsOrdered: Optional[List[str]] = None
    prescription_medicines: Optional[List[Dict[str, str]]] = None
    prescriptionMedicines: Optional[List[Dict[str, str]]] = None
    treatment_plan: Optional[str] = None
    treatmentPlan: Optional[str] = None
    estimated_cost: Optional[int] = None
    estimatedCost: Optional[int] = None

class ConsultationOut(BaseModel):
    id: str
    appointmentId: str
    referenceId: str
    patientId: str
    patientName: str
    doctorId: str
    doctorName: str
    hospitalId: str
    clinicalNotes: str
    diagnosis: str
    investigationsOrdered: List[str]
    prescriptionMedicines: List[Dict[str, str]]
    treatmentPlan: str
    status: str

class ConsultationDraftRequest(BaseModel):
    appointment_id: Optional[str] = None
    appointmentId: Optional[str] = None
    clinical_notes: Optional[str] = None
    clinicalNotes: Optional[str] = None
    diagnosis: Optional[str] = None
    investigations_ordered: Optional[List[str]] = None
    investigationsOrdered: Optional[List[str]] = None
    prescription_medicines: Optional[List[Dict[str, str]]] = None
    prescriptionMedicines: Optional[List[Dict[str, str]]] = None
    treatment_plan: Optional[str] = None
    treatmentPlan: Optional[str] = None

class ConsultationDraftOut(BaseModel):
    id: str
    appointmentId: str
    referenceId: str
    patientId: str
    doctorId: str
    doctorName: str
    hospitalId: str
    clinicalNotes: Optional[str] = None
    diagnosis: Optional[str] = None
    investigationsOrdered: List[str] = []
    prescriptionMedicines: List[Dict[str, str]] = []
    treatmentPlan: Optional[str] = None
    updatedAt: str

# Financial Schemas
class FinancialAssessmentRequest(BaseModel):
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    treatment_cost: Optional[float] = None
    treatmentCost: Optional[float] = None
    hospital_name: Optional[str] = None
    hospitalName: Optional[str] = None
    insurance_coverage: Optional[float] = None
    insuranceCoverage: Optional[float] = None
    government_support: Optional[float] = None
    governmentSupport: Optional[float] = None
    ngo_assistance: Optional[float] = None
    ngoAssistance: Optional[float] = None
    patient_self_contribution: Optional[float] = None
    patientSelfContribution: Optional[float] = None
    has_insurance: Optional[bool] = None
    has_government_card: Optional[bool] = None
    ration_card_type: Optional[str] = None

class FinancialAssessmentResponse(BaseModel):
    id: Optional[str] = None
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    hospital_name: Optional[str] = None
    hospitalName: Optional[str] = None
    estimated_treatment_cost: float
    estimatedTreatmentCost: Optional[float] = None
    insurance_support: float
    insuranceCoverage: Optional[float] = None
    government_support: float
    governmentSupport: Optional[float] = None
    ngo_support: float
    ngoAssistance: Optional[float] = None
    patient_self_contribution: Optional[float] = 0.0
    patientSelfContribution: Optional[float] = 0.0
    estimated_patient_gap: float
    financialGap: Optional[float] = None
    is_funding_complete: Optional[bool] = False
    isFundingComplete: Optional[bool] = False
    calculated_at: Optional[str] = None
    calculatedAt: Optional[str] = None
    disclaimer: str = "Estimates only based on current policy rules. Final approval subject to hospital and provider verification."

class FinancePlanRequest(BaseModel):
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    treatment_cost: Optional[float] = None
    treatmentCost: Optional[float] = None
    insurance_coverage: Optional[float] = 0.0
    insuranceCoverage: Optional[float] = 0.0
    government_support: Optional[float] = 0.0
    governmentSupport: Optional[float] = 0.0
    ngo_support: Optional[float] = 0.0
    ngoSupport: Optional[float] = 0.0
    additional_savings: Optional[float] = 0.0
    additionalSavings: Optional[float] = 0.0

class FinancePlanResponse(BaseModel):
    estimated_cost: float
    estimatedCost: Optional[float] = None
    insurance_benefit: float
    insuranceBenefit: Optional[float] = None
    government_benefit: float
    governmentBenefit: Optional[float] = None
    ngo_benefit: float
    ngoBenefit: Optional[float] = None
    patient_out_of_pocket: float
    patientOutOfPocket: Optional[float] = None
    remaining_gap: float
    remainingGap: Optional[float] = None
    recommendation_tag: str
    recommendationTag: Optional[str] = None
    disclaimer: str

class TreatmentEstimateCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    patientId: Optional[str] = None
    hospital_id: Optional[str] = "hosp-1"
    hospitalId: Optional[str] = None
    hospital_name: Optional[str] = "CarePlus Hospital"
    hospitalName: Optional[str] = None
    procedure_name: Optional[str] = None
    procedureName: Optional[str] = None
    room_category: Optional[str] = "General Ward"
    roomCategory: Optional[str] = None
    estimated_cost_min: Optional[float] = None
    estimatedCostMin: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    estimatedCostMax: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = None
    consultation_id: Optional[str] = None
    consultationId: Optional[str] = None

# Audit Log Schemas
class AuditLogCreate(BaseModel):
    actor_role: str
    actor_id: str
    action: str
    details: str

class AuditLogOut(BaseModel):
    id: str
    timestamp: str
    actorRole: str
    actorId: str
    action: str
    details: str
