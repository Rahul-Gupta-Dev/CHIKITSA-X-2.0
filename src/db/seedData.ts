import type {
  User,
  PatientProfile,
  Hospital,
  Doctor,
  OPDRegistration,
  InsurancePolicy,
  GovernmentScheme,
  NGOSupport
} from '../types';

export const DEMO_USERS: User[] = [
  {
    id: 'usr-patient-1',
    email: 'patient@chikitsax.demo',
    name: 'Ramesh Sharma',
    role: 'PATIENT',
    phone: '+91 98765 43210',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'usr-doctor-1',
    email: 'doctor@chikitsax.demo',
    name: 'Dr. Rajesh Kulkarni',
    role: 'DOCTOR',
    phone: '+91 98220 11223',
    hospitalId: 'hosp-1',
    avatar: 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'usr-hospital-1',
    email: 'hospital@chikitsax.demo',
    name: 'CarePlus Hospital Admin',
    role: 'HOSPITAL_ADMIN',
    phone: '+91 020 6789 0000',
    hospitalId: 'hosp-1',
    avatar: 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=200&q=80'
  }
];

export const INITIAL_PATIENT_PROFILE: PatientProfile = {
  id: 'pat-sharma-1',
  userId: 'usr-patient-1',
  fullName: 'Ramesh Sharma',
  age: 48,
  gender: 'Male',
  bloodGroup: 'B+',
  phone: '+91 98765 43210',
  email: 'patient@chikitsax.demo',
  address: 'Flat 402, Green Acres, Shivajinagar',
  city: 'Pune',
  pincode: '411005',
  emergencyContact: {
    name: 'Sunita Sharma',
    relationship: 'Spouse',
    phone: '+91 98765 43211'
  },
  symptoms: ['Chest Tightness', 'Mild Shortness of Breath', 'Fatigue on Walking'],
  medicalHistory: ['Type 2 Diabetes Mellitus (5 yrs)', 'Mild Hypertension'],
  medications: ['Metformin 500mg BD', 'Telmisartan 40mg OD'],
  allergies: ['Penicillin'],
  vitalSigns: {
    bp: '138/88 mmHg',
    pulse: '84 bpm',
    spo2: '97%',
    temp: '98.4 °F'
  },
  careStage: 6, // Stage 6: OPD Registration Complete
  financialBudgetPreference: 'MEDIUM',
  hasInsurance: true,
  insuranceProvider: 'Star Health Care Policy',
  policyNumber: 'SH-2024-998124',
  hasGovernmentCard: true,
  rationCardType: 'BPL',
  incomeCategory: '< ₹2.5 Lakh / annum'
};

export const SEED_OPD_REGISTRATIONS: OPDRegistration[] = [
  {
    id: 'opd-seed-1',
    referenceId: 'CHX-2026-8A92F',
    patientId: 'usr-patient-1',
    patientName: 'Ramesh Sharma',
    patientPhone: '+91 98765 43210',
    hospitalId: 'hosp-1',
    hospitalName: 'CarePlus Super Specialty Hospital',
    department: 'Cardiology',
    doctorId: 'doc-1',
    doctorName: 'Dr. Rajesh Kulkarni',
    appointmentDate: 'Today (09 Sep 2026)',
    appointmentTime: '11:30 AM',
    consultationFee: 800,
    status: 'CONFIRMED',
    createdAt: new Date().toLocaleDateString('en-IN'),
    qrToken: 'TOKEN_SECURE_CHX-2026-8A92F_1725900000000'
  }
];

export const SEED_HOSPITALS: Hospital[] = [
  {
    id: 'hosp-1',
    name: 'CarePlus Super Specialty Hospital',
    code: 'CPH-PUNE',
    tagline: 'Excellence in Cardiology & Tertiary Emergency Care',
    address: 'Plot 14, Senapati Bapat Road, Shivajinagar',
    city: 'Pune',
    distanceKm: 3.2,
    phone: '+91 020 6789 0000',
    emergencyPhone: '+91 020 6789 9999',
    rating: 4.8,
    reviewCount: 1240,
    emergencyAvailable: true,
    emergencyBedsFree: 6,
    icuBedsFree: 4,
    specialties: ['Cardiology', 'General Medicine', 'Neurology', 'Orthopedics', 'Emergency Trauma'],
    clinicalFitScore: 96,
    affordabilityScore: 88,
    availabilityScore: 92,
    supportServicesScore: 95,
    chikitsaxCareScore: 93,
    estimatedCostRange: { min: 70000, max: 110000 },
    acceptedInsuranceProviders: ['Star Health', 'HDFC ERGO', 'Niva Bupa', 'Care Insurance', 'ICICI Lombard'],
    acceptedGovSchemes: ['Ayushman Bharat (PM-JAY)', 'MJPJAY Maharashtra', 'Central Gov Health Scheme'],
    ngoPartnerships: ['Tata Trusts Healthcare Fund', 'Being Human Foundation', 'Smile Care Assistance'],
    accreditation: ['NABH Accredited', 'JCI Certified', 'NABL Lab'],
    opdSlotAvailability: 'HIGH',
    image: 'https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?auto=format&fit=crop&w=600&q=80',
    whyRecommended: {
      specialtyMatch: 'Top-ranked Cardiology & Cardiac Emergency department within 4 km',
      costFeasibility: 'Full PM-JAY & Star Health cashless coverage bringing out-of-pocket close to ₹0',
      proximityReason: 'Only 3.2 km (approx 10 mins drive)',
      availabilityReason: 'Immediate OPD slots available today with 6 free Emergency Trauma beds',
      financialSupportReason: 'Supports all major Gov schemes and active Tata Trusts NGO desk'
    }
  },
  {
    id: 'hosp-2',
    name: 'Apollo Health City & Emergency Care',
    code: 'APO-PUNE',
    tagline: 'Advanced Cardiac & Multi-Organ Specialty Center',
    address: 'Viman Nagar Main Road, Near Airport Road',
    city: 'Pune',
    distanceKm: 7.8,
    phone: '+91 020 4911 2000',
    emergencyPhone: '+91 020 4911 9111',
    rating: 4.9,
    reviewCount: 2150,
    emergencyAvailable: true,
    emergencyBedsFree: 8,
    icuBedsFree: 5,
    specialties: ['Cardiology', 'Cardiac Surgery', 'Pulmonology', 'Oncology', 'Emergency Medicine'],
    clinicalFitScore: 98,
    affordabilityScore: 72,
    availabilityScore: 85,
    supportServicesScore: 90,
    chikitsaxCareScore: 89,
    estimatedCostRange: { min: 95000, max: 150000 },
    acceptedInsuranceProviders: ['Star Health', 'HDFC ERGO', 'Niva Bupa', 'Max Bupa', 'Aditya Birla Health'],
    acceptedGovSchemes: ['Ayushman Bharat (PM-JAY)', 'State Employee Scheme'],
    ngoPartnerships: ['Being Human Foundation', 'Apollo CSR Health Initiative'],
    accreditation: ['JCI Accredited', 'NABH Gold', 'NABL'],
    opdSlotAvailability: 'MEDIUM',
    image: 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=600&q=80',
    whyRecommended: {
      specialtyMatch: 'Highest clinical excellence rating for Cardiac Interventions',
      costFeasibility: 'Higher baseline cost, but covered under private insurance cashless Desk',
      proximityReason: '7.8 km away via Highway',
      availabilityReason: 'OPD available in afternoon slot',
      financialSupportReason: 'CSR Support available for critical cardiac procedures'
    }
  },
  {
    id: 'hosp-3',
    name: 'AIIMS Regional Referral & Emergency Trauma Center',
    code: 'AIIMS-REG',
    tagline: 'Premier Public Tertiary Care & Research Institute',
    address: 'University Circle Campus, Ganeshkhind Road',
    city: 'Pune',
    distanceKm: 2.1,
    phone: '+91 020 2567 1111',
    emergencyPhone: '+91 020 2567 9999',
    rating: 4.6,
    reviewCount: 3400,
    emergencyAvailable: true,
    emergencyBedsFree: 12,
    icuBedsFree: 2,
    specialties: ['General Medicine', 'Cardiology', 'Pulmonology', 'Emergency Trauma', 'Radiology'],
    clinicalFitScore: 94,
    affordabilityScore: 98,
    availabilityScore: 78,
    supportServicesScore: 85,
    chikitsaxCareScore: 91,
    estimatedCostRange: { min: 12000, max: 35000 },
    acceptedInsuranceProviders: ['All National Insurance Policies', 'Star Health', 'UIIC'],
    acceptedGovSchemes: ['Ayushman Bharat (PM-JAY)', 'MJPJAY', 'EHS', 'RAN Fund'],
    ngoPartnerships: ['Prime Minister Relief Fund', 'Red Cross India', 'Tata Trusts'],
    accreditation: ['Government Super Specialty Center', 'NABL Accredited'],
    opdSlotAvailability: 'HIGH',
    image: 'https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=600&q=80',
    whyRecommended: {
      specialtyMatch: 'Full Cardiology Department with 24x7 Cath Lab',
      costFeasibility: 'Extremely affordable public care with near 100% subsidy under Gov schemes',
      proximityReason: 'Nearest facility at 2.1 km',
      availabilityReason: '24x7 Emergency Triage open now',
      financialSupportReason: 'Complete exemption for BPL ration card holders'
    }
  },
  {
    id: 'hosp-4',
    name: 'City Community Health Center & Cardiac Care',
    code: 'CCH-PUNE',
    tagline: 'Affordable Quality Care for Neighborhood Families',
    address: 'Kothrud Depot Chowk, Karve Road',
    city: 'Pune',
    distanceKm: 4.5,
    phone: '+91 020 2538 4400',
    emergencyPhone: '+91 020 2538 4499',
    rating: 4.4,
    reviewCount: 890,
    emergencyAvailable: false,
    emergencyBedsFree: 0,
    icuBedsFree: 1,
    specialties: ['General Medicine', 'Diabetology', 'Non-invasive Cardiology', 'Internal Medicine'],
    clinicalFitScore: 85,
    affordabilityScore: 92,
    availabilityScore: 90,
    supportServicesScore: 80,
    chikitsaxCareScore: 87,
    estimatedCostRange: { min: 35000, max: 60000 },
    acceptedInsuranceProviders: ['Star Health', 'Care Insurance', 'National Insurance'],
    acceptedGovSchemes: ['Ayushman Bharat (PM-JAY)', 'MJPJAY'],
    ngoPartnerships: ['Smile Foundation', 'Local Health Trust'],
    accreditation: ['NABH Entry Level'],
    opdSlotAvailability: 'HIGH',
    image: 'https://images.unsplash.com/photo-1538108149393-fbbd81895907?auto=format&fit=crop&w=600&q=80',
    whyRecommended: {
      specialtyMatch: 'Great match for routine cardiac evaluation & diabetes management',
      costFeasibility: 'Low cost tier ideal for moderate budget preference',
      proximityReason: '4.5 km from location',
      availabilityReason: 'Short wait time for OPD registration',
      financialSupportReason: 'Empaneled with state health scheme'
    }
  },
  {
    id: 'hosp-5',
    name: 'Fortis Emergency & Critical Trauma Hub',
    code: 'FOR-PUNE',
    tagline: '24/7 Rapid Emergency Response & Intensive Care',
    address: 'Baner-Pashan Link Road, Baner',
    city: 'Pune',
    distanceKm: 5.6,
    phone: '+91 020 6712 3000',
    emergencyPhone: '+91 020 6712 9100',
    rating: 4.7,
    reviewCount: 1650,
    emergencyAvailable: true,
    emergencyBedsFree: 10,
    icuBedsFree: 6,
    specialties: ['Emergency Medicine', 'Interventional Cardiology', 'Critical Care', 'Vascular Surgery'],
    clinicalFitScore: 95,
    affordabilityScore: 78,
    availabilityScore: 95,
    supportServicesScore: 92,
    chikitsaxCareScore: 90,
    estimatedCostRange: { min: 80000, max: 130000 },
    acceptedInsuranceProviders: ['Star Health', 'HDFC ERGO', 'Niva Bupa', 'Bajaj Allianz'],
    acceptedGovSchemes: ['Ayushman Bharat (PM-JAY)'],
    ngoPartnerships: ['Tata Trusts', 'Fortis Foundation'],
    accreditation: ['NABH Accredited', 'NABL'],
    opdSlotAvailability: 'HIGH',
    image: 'https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=600&q=80',
    whyRecommended: {
      specialtyMatch: 'Rapid response emergency protocol for chest discomfort',
      costFeasibility: 'Empaneled with private insurance cashless network',
      proximityReason: '5.6 km quick drive via Western bypass',
      availabilityReason: 'Instant emergency admission desk',
      financialSupportReason: 'Emergency financing assistance desk'
    }
  }
];

export const SEED_DOCTORS: Doctor[] = [
  {
    id: 'doc-1',
    hospitalId: 'hosp-1',
    hospitalName: 'CarePlus Super Specialty Hospital',
    name: 'Dr. Rajesh Kulkarni',
    specialty: 'Senior Interventional Cardiologist',
    qualification: 'MBBS, MD (Med), DM (Cardiology), FACC',
    experienceYears: 18,
    rating: 4.9,
    consultationFee: 800,
    availableDays: ['Today', 'Tomorrow', 'Thursday', 'Friday'],
    availableSlots: ['10:00 AM', '11:30 AM', '02:00 PM', '04:30 PM'],
    avatar: 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'doc-2',
    hospitalId: 'hosp-1',
    hospitalName: 'CarePlus Super Specialty Hospital',
    name: 'Dr. Ananya Roy',
    specialty: 'Consultant Physician & Diabetologist',
    qualification: 'MBBS, MD (Internal Medicine)',
    experienceYears: 12,
    rating: 4.8,
    consultationFee: 600,
    availableDays: ['Today', 'Tomorrow', 'Wednesday'],
    availableSlots: ['09:30 AM', '11:00 AM', '03:00 PM'],
    avatar: 'https://images.unsplash.com/photo-1594824813566-88855ce78905?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'doc-3',
    hospitalId: 'hosp-2',
    hospitalName: 'Apollo Health City',
    name: 'Dr. Vikram Deshmukh',
    specialty: 'Chief Cardiac Surgeon',
    qualification: 'MBBS, MS, MCh (Cardio-Thoracic Surgery)',
    experienceYears: 22,
    rating: 4.95,
    consultationFee: 1200,
    availableDays: ['Tomorrow', 'Thursday'],
    availableSlots: ['11:00 AM', '03:30 PM'],
    avatar: 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'doc-4',
    hospitalId: 'hosp-3',
    hospitalName: 'AIIMS Regional Emergency Center',
    name: 'Dr. Sunita Deshpande',
    specialty: 'Head of Emergency Medicine & Triage',
    qualification: 'MBBS, MD (Emergency Medicine)',
    experienceYears: 15,
    rating: 4.7,
    consultationFee: 200,
    availableDays: ['Today', 'Tomorrow', 'Everyday'],
    availableSlots: ['09:00 AM', '10:30 AM', '01:00 PM', '05:00 PM'],
    avatar: 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=200&q=80'
  }
];

export const SEED_INSURANCE_POLICIES: InsurancePolicy[] = [
  {
    id: 'pol-star-1',
    patientId: 'pat-sharma-1',
    providerName: 'Star Health Comprehensive Policy',
    policyNumber: 'SH-2024-998124',
    sumInsured: 500000,
    availableBalance: 420000,
    coPayPercentage: 10,
    isCashlessAvailable: true,
    status: 'ACTIVE'
  },
  {
    id: 'pol-hdfc-2',
    patientId: 'pat-sharma-1',
    providerName: 'HDFC ERGO Optima Secure',
    policyNumber: 'HDFC-HEALTH-44102',
    sumInsured: 300000,
    availableBalance: 300000,
    coPayPercentage: 0,
    isCashlessAvailable: true,
    status: 'ACTIVE'
  }
];

export const SEED_GOV_SCHEMES: GovernmentScheme[] = [
  {
    id: 'sch-pmjay',
    schemeCode: 'PM-JAY',
    schemeName: 'Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
    description: 'National public health insurance scheme providing free coverage up to ₹5 Lakh per family per year for secondary & tertiary hospital care.',
    maxBenefitAmount: 500000,
    eligibilityCriteria: {
      rationCardTypes: ['AAY', 'BPL'],
      maxAnnualIncome: 250000,
      coveredIllnesses: ['Cardiology', 'Coronary Angiography', 'Cardiac Stenting', 'Oncology', 'Trauma']
    },
    requiredDocuments: ['Ayushman Card / Golden Card', 'Aadhaar Card', 'BPL Ration Card'],
    contactHelpline: '14555'
  },
  {
    id: 'sch-mjpjay',
    schemeCode: 'MJPJAY',
    schemeName: 'Mahatma Jyotirao Phule Jan Arogya Yojana (Maharashtra)',
    description: 'State government scheme providing cashless medical quality care up to ₹1.5 Lakh to ₹5 Lakh for low income families.',
    maxBenefitAmount: 300000,
    eligibilityCriteria: {
      rationCardTypes: ['Yellow', 'Orange', 'BPL'],
      maxAnnualIncome: 300000,
      coveredIllnesses: ['Cardiac Surgery', 'Angioplasty', 'Critical Care']
    },
    requiredDocuments: ['Yellow/Orange Ration Card', 'Aadhaar Card', 'Income Certificate'],
    contactHelpline: '155388'
  }
];

export const SEED_NGO_SUPPORT: NGOSupport[] = [
  {
    id: 'ngo-tata',
    organizationName: 'Tata Trusts Healthcare Assistance Fund',
    supportType: 'Direct Medical Bill Grant',
    maxAssistanceAmount: 30000,
    eligibilityDescription: 'Provides financial gap funding for cardiac and critical care patients with income below ₹3 Lakh.',
    requiredDocuments: ['Hospital Cost Estimate', 'Income Certificate', 'Aadhaar Card'],
    applicationStatus: 'AVAILABLE'
  },
  {
    id: 'ngo-beinghuman',
    organizationName: 'Being Human Healthcare Relief Initiative',
    supportType: 'Specialty Surgery Aid',
    maxAssistanceAmount: 25000,
    eligibilityDescription: 'Special fund for urgent cardiac and pediatric procedures.',
    requiredDocuments: ['Doctor Recommendation Letter', 'Hospital Estimate'],
    applicationStatus: 'AVAILABLE'
  },
  {
    id: 'ngo-smile',
    organizationName: 'Smile Foundation Critical Care Grant',
    supportType: 'Diagnostic & Medication Subsidy',
    maxAssistanceAmount: 15000,
    eligibilityDescription: 'Assistance for expensive diagnostic tests and post-op medicines.',
    requiredDocuments: ['Prescription', 'Hospital Bill Draft'],
    applicationStatus: 'AVAILABLE'
  }
];
