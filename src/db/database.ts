import type {
  User,
  UserRole,
  PatientProfile,
  Hospital,
  Doctor,
  SymptomIntake,
  MedicalRecord,
  TriageResult,
  OPDRegistration,
  QRPassToken,
  PatientConsent,
  Consultation,
  TreatmentCostEstimate,
  InsurancePolicy,
  InsuranceClaim,
  GovernmentScheme,
  NGOSupport,
  CareToCostAssessment,
  AuditLog
} from '../types';
import {
  DEMO_USERS,
  INITIAL_PATIENT_PROFILE,
  SEED_HOSPITALS,
  SEED_DOCTORS,
  SEED_OPD_REGISTRATIONS,
  SEED_INSURANCE_POLICIES,
  SEED_GOV_SCHEMES,
  SEED_NGO_SUPPORT
} from './seedData';

const STORAGE_KEYS = {
  CURRENT_USER: 'chikitsax_current_user',
  PATIENT_PROFILE: 'chikitsax_patient_profile',
  SYMPTOM_INTAKES: 'chikitsax_symptom_intakes',
  MEDICAL_RECORDS: 'chikitsax_medical_records',
  TRIAGE_RESULTS: 'chikitsax_triage_results',
  HOSPITALS: 'chikitsax_hospitals',
  DOCTORS: 'chikitsax_doctors',
  OPD_REGISTRATIONS: 'chikitsax_opd_registrations',
  QR_TOKENS: 'chikitsax_qr_tokens',
  CONSENTS: 'chikitsax_consents',
  CONSULTATIONS: 'chikitsax_consultations',
  COST_ESTIMATES: 'chikitsax_cost_estimates',
  INSURANCE_POLICIES: 'chikitsax_insurance_policies',
  INSURANCE_CLAIMS: 'chikitsax_insurance_claims',
  GOV_SCHEMES: 'chikitsax_gov_schemes',
  NGO_SUPPORT: 'chikitsax_ngo_support',
  FINANCE_ASSESSMENTS: 'chikitsax_finance_assessments',
  AUDIT_LOGS: 'chikitsax_audit_logs'
};

class LocalDB {
  private getStorage<T>(key: string, defaultVal: T): T {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : defaultVal;
    } catch {
      return defaultVal;
    }
  }

  private setStorage<T>(key: string, val: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) {
      console.error('Storage save error:', e);
    }
  }

  constructor() {
    this.init();
  }

  public init() {
    if (!localStorage.getItem(STORAGE_KEYS.CURRENT_USER)) {
      this.setStorage(STORAGE_KEYS.CURRENT_USER, DEMO_USERS[0]);
    }
    if (!localStorage.getItem(STORAGE_KEYS.PATIENT_PROFILE)) {
      this.setStorage(STORAGE_KEYS.PATIENT_PROFILE, INITIAL_PATIENT_PROFILE);
    }
    if (!localStorage.getItem(STORAGE_KEYS.HOSPITALS)) {
      this.setStorage(STORAGE_KEYS.HOSPITALS, SEED_HOSPITALS);
    }
    if (!localStorage.getItem(STORAGE_KEYS.DOCTORS)) {
      this.setStorage(STORAGE_KEYS.DOCTORS, SEED_DOCTORS);
    }
    if (!localStorage.getItem(STORAGE_KEYS.INSURANCE_POLICIES)) {
      this.setStorage(STORAGE_KEYS.INSURANCE_POLICIES, SEED_INSURANCE_POLICIES);
    }
    if (!localStorage.getItem(STORAGE_KEYS.GOV_SCHEMES)) {
      this.setStorage(STORAGE_KEYS.GOV_SCHEMES, SEED_GOV_SCHEMES);
    }
    if (!localStorage.getItem(STORAGE_KEYS.NGO_SUPPORT)) {
      this.setStorage(STORAGE_KEYS.NGO_SUPPORT, SEED_NGO_SUPPORT);
    }
    if (!localStorage.getItem(STORAGE_KEYS.OPD_REGISTRATIONS)) {
      this.setStorage(STORAGE_KEYS.OPD_REGISTRATIONS, SEED_OPD_REGISTRATIONS);
    }
    if (!localStorage.getItem(STORAGE_KEYS.CONSENTS)) {
      this.setStorage(STORAGE_KEYS.CONSENTS, []);
    }
    if (!localStorage.getItem(STORAGE_KEYS.CONSULTATIONS)) {
      this.setStorage(STORAGE_KEYS.CONSULTATIONS, []);
    }
    if (!localStorage.getItem(STORAGE_KEYS.COST_ESTIMATES)) {
      this.setStorage(STORAGE_KEYS.COST_ESTIMATES, []);
    }
    if (!localStorage.getItem(STORAGE_KEYS.AUDIT_LOGS)) {
      this.logAudit('PATIENT', 'usr-patient-1', 'SYSTEM_INIT', 'Database initialized with demo seed dataset.');
    }
  }

  // User & Auth
  public getCurrentUser(): User | null {
    const token = localStorage.getItem('chikitsax_auth_token');
    const user = this.getStorage<User | null>(STORAGE_KEYS.CURRENT_USER, null);
    if (!token && !user) {
      return null;
    }
    return user;
  }

  public setCurrentUser(user: User | null): void {
    if (!user) {
      this.clearCurrentUser();
      return;
    }
    this.setStorage(STORAGE_KEYS.CURRENT_USER, user);
    this.logAudit(user.role, user.id, 'SWITCH_ROLE', `Active role switched to ${user.role} (${user.email})`);
  }

  public clearCurrentUser(): void {
    localStorage.removeItem(STORAGE_KEYS.CURRENT_USER);
    localStorage.removeItem('chikitsax_auth_token');
  }

  public getDemoUsers(): User[] {
    return DEMO_USERS;
  }

  // Patient Profile
  public getPatientProfile(): PatientProfile {
    return this.getStorage<PatientProfile>(STORAGE_KEYS.PATIENT_PROFILE, INITIAL_PATIENT_PROFILE);
  }

  public updatePatientProfile(updated: Partial<PatientProfile>): PatientProfile {
    const current = this.getPatientProfile();
    const newProfile = { ...current, ...updated };
    this.setStorage(STORAGE_KEYS.PATIENT_PROFILE, newProfile);
    this.logAudit('PATIENT', current.userId, 'UPDATE_HEALTH_PROFILE', 'Updated unified health profile parameters');
    return newProfile;
  }

  public updateCareStage(stage: number): void {
    const profile = this.getPatientProfile();
    if (stage > profile.careStage) {
      profile.careStage = stage;
      this.setStorage(STORAGE_KEYS.PATIENT_PROFILE, profile);
      this.logAudit('PATIENT', profile.userId, 'CARE_STAGE_PROGRESS', `Care journey progressed to stage ${stage}`);
    }
  }

  // Symptom Intakes
  public addSymptomIntake(intake: SymptomIntake): void {
    const list = this.getStorage<SymptomIntake[]>(STORAGE_KEYS.SYMPTOM_INTAKES, []);
    list.unshift(intake);
    this.setStorage(STORAGE_KEYS.SYMPTOM_INTAKES, list);

    // Update patient profile symptoms
    const profile = this.getPatientProfile();
    const merged = Array.from(new Set([...profile.symptoms, ...intake.extractedSymptoms]));
    this.updatePatientProfile({ symptoms: merged });
    this.updateCareStage(2);
    this.logAudit('PATIENT', intake.patientId, 'AI_VOICE_INTAKE', `Recorded intake: ${intake.extractedSymptoms.join(', ')}`);
  }

  public getSymptomIntakes(): SymptomIntake[] {
    return this.getStorage<SymptomIntake[]>(STORAGE_KEYS.SYMPTOM_INTAKES, []);
  }

  // Medical Records OCR
  public addMedicalRecord(record: MedicalRecord): void {
    const list = this.getStorage<MedicalRecord[]>(STORAGE_KEYS.MEDICAL_RECORDS, []);
    list.unshift(record);
    this.setStorage(STORAGE_KEYS.MEDICAL_RECORDS, list);

    // Sync extracted data to profile
    const profile = this.getPatientProfile();
    const newMedications = record.ocrExtractedData.medicinesExtracted || [];
    const newAllergies = record.ocrExtractedData.allergiesExtracted || [];
    const mergedMeds = Array.from(new Set([...profile.medications, ...newMedications]));
    const mergedAllergies = Array.from(new Set([...profile.allergies, ...newAllergies]));
    
    this.updatePatientProfile({
      medications: mergedMeds,
      allergies: mergedAllergies
    });
    this.updateCareStage(3);
    this.logAudit('PATIENT', record.patientId, 'UPLOAD_OCR_RECORD', `Processed OCR record: ${record.fileName} (${record.category})`);
  }

  public getMedicalRecords(): MedicalRecord[] {
    return this.getStorage<MedicalRecord[]>(STORAGE_KEYS.MEDICAL_RECORDS, []);
  }

  // Triage Results
  public saveTriageResult(triage: TriageResult): void {
    const list = this.getStorage<TriageResult[]>(STORAGE_KEYS.TRIAGE_RESULTS, []);
    list.unshift(triage);
    this.setStorage(STORAGE_KEYS.TRIAGE_RESULTS, list);
    this.updateCareStage(4);
    this.logAudit('PATIENT', triage.patientId, 'AI_TRIAGE', `Triage generated: Risk ${triage.riskLevel}, Urgency: ${triage.urgency}`);
  }

  public getLatestTriage(): TriageResult | null {
    const list = this.getStorage<TriageResult[]>(STORAGE_KEYS.TRIAGE_RESULTS, []);
    return list.length > 0 ? list[0] : null;
  }

  // Hospitals & Doctors
  public getHospitals(): Hospital[] {
    return this.getStorage<Hospital[]>(STORAGE_KEYS.HOSPITALS, SEED_HOSPITALS);
  }

  public getDoctors(hospitalId?: string): Doctor[] {
    const list = this.getStorage<Doctor[]>(STORAGE_KEYS.DOCTORS, SEED_DOCTORS);
    return hospitalId ? list.filter(d => d.hospitalId === hospitalId) : list;
  }

  // OPD Registrations
  public createOPDRegistration(opd: OPDRegistration): void {
    const list = this.getStorage<OPDRegistration[]>(STORAGE_KEYS.OPD_REGISTRATIONS, SEED_OPD_REGISTRATIONS);
    list.unshift(opd);
    this.setStorage(STORAGE_KEYS.OPD_REGISTRATIONS, list);

    // Save QR token reference
    const qrTokens = this.getStorage<QRPassToken[]>(STORAGE_KEYS.QR_TOKENS, []);
    qrTokens.unshift({
      id: `qr-${opd.id}`,
      referenceId: opd.referenceId,
      token: opd.qrToken,
      patientId: opd.patientId,
      hospitalId: opd.hospitalId,
      expiresAt: new Date(Date.now() + 86400000).toISOString(),
      isVerified: false
    });
    this.setStorage(STORAGE_KEYS.QR_TOKENS, qrTokens);

    this.updateCareStage(6);
    this.logAudit('PATIENT', opd.patientId, 'OPD_BOOKED', `Booked OPD ${opd.referenceId} at ${opd.hospitalName} with ${opd.doctorName}`);
  }

  public getOPDRegistrations(): OPDRegistration[] {
    return this.getStorage<OPDRegistration[]>(STORAGE_KEYS.OPD_REGISTRATIONS, SEED_OPD_REGISTRATIONS);
  }

  public getOPDByRefId(refId: string): OPDRegistration | undefined {
    const list = this.getOPDRegistrations();
    return list.find(o => o.referenceId.trim().toUpperCase() === refId.trim().toUpperCase());
  }

  public verifyQRPass(refId: string, staffName: string): { success: boolean; opd?: OPDRegistration; message: string } {
    const opd = this.getOPDByRefId(refId);
    if (!opd) {
      return { success: false, message: `Reference ID ${refId} not found in hospital system.` };
    }

    opd.status = 'VERIFIED';
    const list = this.getOPDRegistrations();
    const idx = list.findIndex(o => o.id === opd.id);
    if (idx !== -1) list[idx] = opd;
    this.setStorage(STORAGE_KEYS.OPD_REGISTRATIONS, list);

    // Update QR token status
    const qrTokens = this.getStorage<QRPassToken[]>(STORAGE_KEYS.QR_TOKENS, []);
    const qToken = qrTokens.find(q => q.referenceId.trim().toUpperCase() === refId.trim().toUpperCase());
    if (qToken) {
      qToken.isVerified = true;
      qToken.verifiedAt = new Date().toISOString();
      qToken.verifiedByStaff = staffName;
      this.setStorage(STORAGE_KEYS.QR_TOKENS, qrTokens);
    }

    // Auto-create consent request
    this.requestConsent(opd.patientId, opd.hospitalId, opd.hospitalName, opd.doctorId, opd.doctorName);

    this.logAudit('HOSPITAL_ADMIN', 'usr-hospital-1', 'QR_VERIFICATION', `Verified appointment ${refId} for patient ${opd.patientName}`);
    return { success: true, opd, message: `Successfully verified appointment for ${opd.patientName}` };
  }

  public updateOPDStatus(appointmentId: string, status: 'CONFIRMED' | 'VERIFIED' | 'COMPLETED' | 'CANCELLED'): void {
    const list = this.getOPDRegistrations();
    const idx = list.findIndex(o => o.id === appointmentId || o.referenceId === appointmentId);
    if (idx !== -1) {
      list[idx].status = status;
      this.setStorage(STORAGE_KEYS.OPD_REGISTRATIONS, list);
      this.logAudit('PATIENT', list[idx].patientId, 'OPD_STATUS_UPDATE', `Updated OPD ${list[idx].referenceId} status to ${status}`);
    }
  }

  public rescheduleOPD(appointmentId: string, newDate: string, newTime: string): void {
    const list = this.getOPDRegistrations();
    const idx = list.findIndex(o => o.id === appointmentId || o.referenceId === appointmentId);
    if (idx !== -1) {
      list[idx].appointmentDate = newDate;
      list[idx].appointmentTime = newTime;
      list[idx].status = 'CONFIRMED';
      this.setStorage(STORAGE_KEYS.OPD_REGISTRATIONS, list);
      this.logAudit('PATIENT', list[idx].patientId, 'OPD_RESCHEDULED', `Rescheduled OPD ${list[idx].referenceId} to ${newDate} ${newTime}`);
    }
  }

  // Patient Consents
  public requestConsent(patientId: string, hospitalId: string, hospitalName: string, doctorId?: string, doctorName?: string): PatientConsent {
    const list = this.getStorage<PatientConsent[]>(STORAGE_KEYS.CONSENTS, []);
    const existing = list.find(c => c.patientId === patientId && c.hospitalId === hospitalId && c.status === 'PENDING');
    if (existing) return existing;

    const consent: PatientConsent = {
      id: `cst-${Date.now()}`,
      patientId,
      hospitalId,
      hospitalName,
      doctorId,
      doctorName,
      requestedAt: new Date().toISOString(),
      status: 'PENDING',
      accessibleSections: ['PROFILE', 'SYMPTOMS', 'OCR_RECORDS', 'TRIAGE']
    };
    list.unshift(consent);
    this.setStorage(STORAGE_KEYS.CONSENTS, list);
    return consent;
  }

  public getConsents(): PatientConsent[] {
    return this.getStorage<PatientConsent[]>(STORAGE_KEYS.CONSENTS, []);
  }

  public updateConsentStatus(consentId: string, status: 'GRANTED' | 'REVOKED'): void {
    const list = this.getConsents();
    const consent = list.find(c => c.id === consentId);
    if (consent) {
      consent.status = status;
      if (status === 'GRANTED') {
        consent.grantedAt = new Date().toISOString();
        this.updateCareStage(7);
      }
      this.setStorage(STORAGE_KEYS.CONSENTS, list);
      this.logAudit('PATIENT', consent.patientId, 'CONSENT_UPDATE', `Consent ${status} for ${consent.hospitalName}`);
    }
  }

  public isConsentGranted(patientId: string, hospitalId: string): boolean {
    const list = this.getConsents();
    return list.some(c => c.patientId === patientId && c.hospitalId === hospitalId && c.status === 'GRANTED');
  }

  // Doctor Consultations & Cost Estimates
  public addConsultation(consultation: Consultation): void {
    const list = this.getStorage<Consultation[]>(STORAGE_KEYS.CONSULTATIONS, []);
    list.unshift(consultation);
    this.setStorage(STORAGE_KEYS.CONSULTATIONS, list);
    this.updateCareStage(8);
    this.logAudit('DOCTOR', consultation.doctorId, 'ADD_CONSULTATION', `Clinical notes & treatment plan saved for ${consultation.patientName}`);
  }

  public getConsultations(): Consultation[] {
    return this.getStorage<Consultation[]>(STORAGE_KEYS.CONSULTATIONS, []);
  }

  public saveCostEstimate(estimate: TreatmentCostEstimate): void {
    const list = this.getStorage<TreatmentCostEstimate[]>(STORAGE_KEYS.COST_ESTIMATES, []);
    list.unshift(estimate);
    this.setStorage(STORAGE_KEYS.COST_ESTIMATES, list);
    this.updateCareStage(9);
    this.logAudit('DOCTOR', 'usr-doctor-1', 'GENERATE_COST_ESTIMATE', `Generated estimate ₹${estimate.estimatedCostRange.min} - ₹${estimate.estimatedCostRange.max} for procedure ${estimate.procedureName}`);
  }

  public getLatestCostEstimate(): TreatmentCostEstimate | null {
    const list = this.getStorage<TreatmentCostEstimate[]>(STORAGE_KEYS.COST_ESTIMATES, []);
    return list.length > 0 ? list[0] : null;
  }

  // Insurance, Gov Schemes, NGO Assistance
  public getInsurancePolicies(): InsurancePolicy[] {
    return this.getStorage<InsurancePolicy[]>(STORAGE_KEYS.INSURANCE_POLICIES, SEED_INSURANCE_POLICIES);
  }

  public createInsuranceClaim(claim: InsuranceClaim): void {
    const list = this.getStorage<InsuranceClaim[]>(STORAGE_KEYS.INSURANCE_CLAIMS, []);
    list.unshift(claim);
    this.setStorage(STORAGE_KEYS.INSURANCE_CLAIMS, list);
    this.updateCareStage(10);
    this.logAudit('PATIENT', claim.patientId, 'SUBMIT_INSURANCE_CLAIM', `Claim ${claim.claimReferenceNumber} submitted for ₹${claim.claimedAmount}`);
  }

  public getInsuranceClaims(): InsuranceClaim[] {
    return this.getStorage<InsuranceClaim[]>(STORAGE_KEYS.INSURANCE_CLAIMS, []);
  }

  public getGovSchemes(): GovernmentScheme[] {
    return this.getStorage<GovernmentScheme[]>(STORAGE_KEYS.GOV_SCHEMES, SEED_GOV_SCHEMES);
  }

  public getNGOSupport(): NGOSupport[] {
    return this.getStorage<NGOSupport[]>(STORAGE_KEYS.NGO_SUPPORT, SEED_NGO_SUPPORT);
  }

  public updateNGOStatus(ngoId: string, status: 'APPLIED' | 'APPROVED'): void {
    const list = this.getNGOSupport();
    const ngo = list.find(n => n.id === ngoId);
    if (ngo) {
      ngo.applicationStatus = status;
      this.setStorage(STORAGE_KEYS.NGO_SUPPORT, list);
      this.logAudit('PATIENT', 'usr-patient-1', 'NGO_APPLICATION', `Applied for NGO funding: ${ngo.organizationName}`);
    }
  }

  // Care-to-Cost Assessment
  public saveCareToCostAssessment(assessment: CareToCostAssessment): void {
    const list = this.getStorage<CareToCostAssessment[]>(STORAGE_KEYS.FINANCE_ASSESSMENTS, []);
    list.unshift(assessment);
    this.setStorage(STORAGE_KEYS.FINANCE_ASSESSMENTS, list);
    this.updateCareStage(11);
    this.logAudit('PATIENT', assessment.patientId, 'CARE_TO_COST_CALC', `Financial Gap calculated: ₹${assessment.financialGap}`);
  }

  public getLatestCareToCostAssessment(): CareToCostAssessment | null {
    const list = this.getStorage<CareToCostAssessment[]>(STORAGE_KEYS.FINANCE_ASSESSMENTS, []);
    return list.length > 0 ? list[0] : null;
  }

  // Audit Logs
  public logAudit(actorRole: UserRole, actorId: string, action: string, details: string): void {
    const list = this.getStorage<AuditLog[]>(STORAGE_KEYS.AUDIT_LOGS, []);
    const log: AuditLog = {
      id: `log-${Date.now()}-${Math.floor(Math.random()*1000)}`,
      timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      actorRole,
      actorId,
      action,
      details
    };
    list.unshift(log);
    // Keep max 50 logs
    this.setStorage(STORAGE_KEYS.AUDIT_LOGS, list.slice(0, 50));
  }

  public getAuditLogs(): AuditLog[] {
    return this.getStorage<AuditLog[]>(STORAGE_KEYS.AUDIT_LOGS, []);
  }

  public resetDemoState(): void {
    localStorage.clear();
    this.init();
  }
}

export const db = new LocalDB();
