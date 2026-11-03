export type UserRole = 'PATIENT' | 'DOCTOR' | 'HOSPITAL_ADMIN';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
  phone?: string;
  hospitalId?: string; // For HOSPITAL_ADMIN or DOCTOR
  doctorProfile?: any;
  patientProfile?: any;
  hospitalProfile?: any;
}

export interface PatientProfile {
  id: string;
  userId: string;
  fullName: string;
  age: number;
  gender: string;
  bloodGroup: string;
  phone: string;
  email: string;
  address: string;
  city: string;
  pincode: string;
  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };
  symptoms: string[];
  medicalHistory: string[];
  medications: string[];
  allergies: string[];
  vitalSigns?: {
    bp?: string;
    pulse?: string;
    spo2?: string;
    temp?: string;
  };
  careStage: number; // 1 to 12
  financialBudgetPreference: 'LOW' | 'MEDIUM' | 'HIGH';
  hasInsurance: boolean;
  insuranceProvider?: string;
  policyNumber?: string;
  hasGovernmentCard: boolean;
  rationCardType?: 'AAY' | 'BPL' | 'APL';
  incomeCategory?: string;
}

export interface SymptomIntake {
  id: string;
  patientId: string;
  timestamp: string;
  rawTranscript: string;
  extractedSymptoms: string[];
  duration: string;
  severity: 'Mild' | 'Moderate' | 'Severe' | 'Critical';
  affectedBodyPart?: string;
  triggerEvent?: string;
  isEmergencyAlert: boolean;
}

export interface MedicalRecord {
  id: string;
  patientId: string;
  fileName: string;
  fileType: 'PDF' | 'JPG' | 'PNG';
  category: 'Prescription' | 'Lab Report' | 'Discharge Summary' | 'Radiology Report' | 'Other';
  uploadDate: string;
  ocrExtractedData: {
    previousCondition?: string;
    medicinesExtracted?: string[];
    labResults?: { testName: string; value: string; unit: string; range: string }[];
    allergiesExtracted?: string[];
    diagnosisExtracted?: string;
    doctorName?: string;
    hospitalName?: string;
    ocrAdapterStatus?: string;
    ocrNote?: string;
  };
  isVerifiedByPatient: boolean;
}

export interface TriageResult {
  id: string;
  patientId: string;
  timestamp: string;
  riskLevel: 'LOW' | 'MODERATE' | 'HIGH';
  urgency: 'Routine Consultation' | 'Prompt Consultation (24h)' | 'Urgent Evaluation (Immediate)';
  symptomsConsidered: string[];
  clinicalReasoning: string[];
  recommendedSpecialty: string;
  recommendedNextStep: string;
  isEmergencyTriggered: boolean;
}

export interface Hospital {
  id: string;
  name: string;
  code: string;
  tagline: string;
  address: string;
  city: string;
  distanceKm: number;
  phone: string;
  emergencyPhone: string;
  rating: number;
  reviewCount: number;
  emergencyAvailable: boolean;
  emergencyBedsFree: number;
  icuBedsFree: number;
  specialties: string[];
  clinicalFitScore: number; // 0 to 100
  affordabilityScore: number; // 0 to 100
  availabilityScore: number; // 0 to 100
  supportServicesScore: number; // 0 to 100
  chikitsaxCareScore: number; // Calculated total
  care_score?: number;
  score_breakdown?: Record<string, number>;
  estimatedCostRange: {
    min: number;
    max: number;
  };
  acceptedInsuranceProviders: string[];
  acceptedGovSchemes: string[];
  ngoPartnerships: string[];
  accreditation: string[];
  opdSlotAvailability: 'HIGH' | 'MEDIUM' | 'LOW';
  image: string;
  whyRecommended: {
    specialtyMatch: string;
    costFeasibility: string;
    proximityReason: string;
    availabilityReason: string;
    financialSupportReason: string;
  };
}

export interface DoctorScheduleItem {
  day: string;
  time: string;
  slots: number;
  isBlocked: boolean;
}

export interface BlockedSlotInfo {
  slot?: string;
  date?: string;
  time?: string;
  day?: string;
  reason?: string;
  blockedAt?: string;
}

export interface SlotAvailability {
  time: string;
  isAvailable: boolean;
  isBlocked: boolean;
  isBooked: boolean;
}

export interface DoctorAvailability {
  doctorId: string;
  date: string;
  day?: string;
  isDayBlocked: boolean;
  slots: SlotAvailability[];
}

export interface Doctor {
  id: string;
  hospitalId: string;
  hospitalName: string;
  name: string;
  specialty: string;
  qualification: string;
  experienceYears: number;
  rating: number;
  consultationFee: number;
  availableDays: string[];
  availableSlots: string[];
  weeklySchedule?: DoctorScheduleItem[];
  blockedSlots?: (BlockedSlotInfo | string)[];
  avatar: string;
}

export interface OPDRegistration {
  id: string;
  referenceId: string; // CHX-2026-XXXXXX
  patientId: string;
  patientName: string;
  patientPhone: string;
  hospitalId: string;
  hospitalName: string;
  department: string;
  doctorId: string;
  doctorName: string;
  appointmentDate: string;
  appointmentTime: string;
  consultationFee: number;
  status: 'CONFIRMED' | 'VERIFIED' | 'COMPLETED' | 'CANCELLED';
  createdAt: string;
  qrToken: string;
}

export interface QRPassToken {
  id: string;
  referenceId: string;
  token: string;
  patientId: string;
  hospitalId: string;
  expiresAt: string;
  isVerified: boolean;
  verifiedAt?: string;
  verifiedByStaff?: string;
}

export interface PatientConsent {
  id: string;
  patientId: string;
  hospitalId: string;
  hospitalName: string;
  doctorId?: string;
  doctorName?: string;
  requestedAt: string;
  grantedAt?: string;
  status: 'PENDING' | 'GRANTED' | 'REVOKED';
  accessibleSections: ('PROFILE' | 'SYMPTOMS' | 'OCR_RECORDS' | 'TRIAGE')[];
}

export interface Consultation {
  id: string;
  appointmentId: string;
  referenceId: string;
  patientId: string;
  patientName: string;
  doctorId: string;
  doctorName: string;
  hospitalId: string;
  timestamp: string;
  clinicalNotes: string;
  diagnosis: string;
  investigationsOrdered: string[];
  prescriptionMedicines: { name: string; dosage: string; duration: string }[];
  treatmentPlan: string;
  treatmentCostEstimateId?: string;
  status: 'IN_PROGRESS' | 'COMPLETED';
}

export interface TreatmentCostEstimate {
  id: string;
  consultationId?: string;
  patientId: string;
  hospitalId: string;
  hospitalName: string;
  procedureName: string;
  roomCategory: string;
  estimatedCostRange: {
    min: number;
    max: number;
  };
  breakdown: {
    procedureCost: number;
    roomCharges: number;
    investigationCost: number;
    medicationCost: number;
    otherCharges: number;
  };
  confidenceLevel: 'HIGH' | 'MEDIUM' | 'INDICATIVE';
  createdAt: string;
}

export interface InsurancePolicy {
  id: string;
  patientId: string;
  providerName: string;
  policyNumber: string;
  sumInsured: number;
  availableBalance: number;
  coPayPercentage: number;
  isCashlessAvailable: boolean;
  status: 'ACTIVE' | 'EXPIRED' | 'CLAIM_PENDING';
}

export interface InsuranceClaim {
  id: string;
  patientId: string;
  policyId: string;
  treatmentCostEstimateId: string;
  claimedAmount: number;
  approvedAmount?: number;
  status: 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED';
  submittedAt: string;
  claimReferenceNumber: string;
}

export interface GovernmentScheme {
  id: string;
  schemeCode: string;
  schemeName: string;
  description: string;
  maxBenefitAmount: number;
  eligibilityCriteria: {
    rationCardTypes: string[];
    maxAnnualIncome: number;
    coveredIllnesses: string[];
  };
  requiredDocuments: string[];
  contactHelpline: string;
}

export interface SchemeEligibilityResult {
  schemeId: string;
  schemeName: string;
  isEligible: boolean;
  matchingCriteria: string[];
  potentialSupportAmount: number;
  applicationStatus: 'NOT_APPLIED' | 'APPLIED' | 'VERIFIED' | 'APPROVED';
}

export interface NGOSupport {
  id: string;
  organizationName: string;
  supportType: string;
  maxAssistanceAmount: number;
  eligibilityDescription: string;
  requiredDocuments: string[];
  applicationStatus: 'AVAILABLE' | 'APPLIED' | 'APPROVED';
}

export interface CareToCostAssessment {
  id: string;
  patientId: string;
  hospitalName: string;
  estimatedTreatmentCost: number;
  insuranceCoverage: number;
  governmentSupport: number;
  ngoAssistance: number;
  patientSelfContribution: number;
  financialGap: number;
  isFundingComplete: boolean;
  calculatedAt: string;
}

export interface FinanceScenario {
  id: string;
  scenarioTitle: string;
  hospitalName: string;
  estimatedCost: number;
  insuranceBenefit: number;
  governmentBenefit: number;
  ngoBenefit: number;
  patientOutofPocket: number;
  remainingGap: number;
  recommendationTag: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  actorRole: UserRole;
  actorId: string;
  action: string;
  details: string;
}
