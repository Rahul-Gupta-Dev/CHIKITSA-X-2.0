import type {
  SymptomIntake,
  MedicalRecord,
  TriageResult,
  Hospital,
  Doctor,
  DoctorScheduleItem,
  BlockedSlotInfo,
  DoctorAvailability,
  PatientProfile,
  PatientConsent,
  Consultation,
  OPDRegistration,
  TreatmentCostEstimate,
  SchemeEligibilityResult,
  CareToCostAssessment,
  FinanceScenario,
  GovernmentScheme,
  NGOSupport
} from '../types';
import { db } from '../db/database';
import { apiClient } from './apiClient';

/**
 * Real FastAPI Backend Services with LocalDB Fallback (Phase 1B)
 */
export const authService = {
  login: async (email: string, password: string, role?: string): Promise<{ token: string; user: any }> => {
    const res = await apiClient.post<any>('/auth/login', { email, password, role });
    if (!res || !res.accessToken) {
      throw new Error('Authentication failed: No access token received from server.');
    }
    try {
      localStorage.setItem('chikitsax_auth_token', res.accessToken);
    } catch {
      // ignore storage failure
    }
    return {
      token: res.accessToken,
      user: res.user
    };
  },

  register: async (data: {
    email: string;
    password: string;
    name?: string;
    fullName?: string;
    role?: string;
    phone?: string;
    age?: number;
    gender?: string;
    bloodGroup?: string;
    city?: string;
    hospitalId?: string;
  }): Promise<{ token: string; user: any }> => {
    const res = await apiClient.post<any>('/auth/register', data);
    if (!res || !res.accessToken) {
      throw new Error('Registration failed: No access token received from server.');
    }
    try {
      localStorage.setItem('chikitsax_auth_token', res.accessToken);
    } catch {
      // ignore storage failure
    }
    return {
      token: res.accessToken,
      user: res.user
    };
  },

  getCurrentUser: async (): Promise<any | null> => {
    try {
      return await apiClient.get<any>('/auth/me');
    } catch (err) {
      return null;
    }
  },

  logout: () => {
    try {
      localStorage.removeItem('chikitsax_auth_token');
    } catch {
      // ignore storage failure
    }
  }
};

export const patientService = {
  getProfile: async (patientId?: string): Promise<PatientProfile> => {
    const user = db.getCurrentUser();
    const isDoctorOrStaff = user?.role === 'DOCTOR' || user?.role === 'HOSPITAL_ADMIN' || (user?.role as string) === 'HOSPITAL_STAFF';
    const pid = patientId || (isDoctorOrStaff ? '' : user?.id || 'me');
    if (!pid) {
      throw new Error('Patient ID is required to fetch patient profile');
    }

    try {
      const data = await apiClient.get<any>(`/patients/${pid}/profile`);
      if (data && (data.id || data.userId)) {
        const prof: PatientProfile = {
          id: data.id || 'pat-1',
          userId: data.userId || data.user_id || pid,
          fullName: data.fullName || data.full_name || '',
          age: data.age || 0,
          gender: data.gender || 'Other',
          bloodGroup: data.bloodGroup || data.blood_group || 'O+',
          phone: data.phone || '',
          email: data.email || '',
          address: data.address || '',
          city: data.city || '',
          pincode: data.pincode || '',
          emergencyContact: data.emergencyContact || data.emergency_contact || { name: '', relationship: '', phone: '' },
          symptoms: data.symptoms || [],
          medicalHistory: data.medicalHistory || data.medical_history || [],
          medications: data.medications || [],
          allergies: data.allergies || [],
          vitalSigns: data.vitalSigns || data.vital_signs,
          careStage: data.careStage || data.care_stage || 1,
          financialBudgetPreference: data.financialBudgetPreference || data.financial_budget_preference || 'MEDIUM',
          hasInsurance: Boolean(data.hasInsurance ?? data.has_insurance),
          insuranceProvider: data.insuranceProvider || data.insurance_provider,
          policyNumber: data.policyNumber || data.policy_number,
          hasGovernmentCard: Boolean(data.hasGovernmentCard ?? data.has_government_card),
          rationCardType: data.rationCardType || data.ration_card_type,
          incomeCategory: data.incomeCategory || data.income_category
        };
        // Only update local session profile if the current user is the patient themselves
        if (user?.role === 'PATIENT' && (!patientId || patientId === 'me' || patientId === user?.id)) {
          db.updatePatientProfile(prof);
        }
        return prof;
      }
    } catch (err: any) {
      // If a doctor or hospital requests patient profile, never substitute demo data
      if (patientId || isDoctorOrStaff) {
        throw err;
      }
      console.warn('[patientService] FastAPI endpoint error, falling back to local session profile for patient:', err);
      return db.getPatientProfile();
    }
    throw new Error('Patient profile not found');
  },

  updateProfile: async (updatedFields: Partial<PatientProfile>, patientId?: string): Promise<PatientProfile> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const data = await apiClient.put<any>(`/patients/${pid}`, updatedFields);
      db.updatePatientProfile(updatedFields);
      if (data && (data.id || data.userId)) {
        return {
          ...db.getPatientProfile(),
          fullName: data.fullName || data.full_name || updatedFields.fullName || db.getPatientProfile().fullName,
          age: data.age ?? updatedFields.age ?? db.getPatientProfile().age,
          bloodGroup: data.bloodGroup || data.blood_group || updatedFields.bloodGroup || db.getPatientProfile().bloodGroup
        };
      }
    } catch (err) {
      console.warn('[patientService] FastAPI update failed, syncing local state:', err);
      throw err;
    }
    return db.updatePatientProfile(updatedFields);
  }
};

export const hospitalService = {
  getHospitals: async (): Promise<Hospital[]> => {
    try {
      const data = await apiClient.get<Hospital[]>('/hospitals');
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
    } catch (err) {
      console.warn('[hospitalService] FastAPI /hospitals endpoint unavailable, falling back to LocalDB:', err);
    }
    return db.getHospitals();
  },

  getHospitalById: async (id: string): Promise<Hospital | undefined> => {
    try {
      const data = await apiClient.get<Hospital>(`/hospitals/${id}`);
      if (data && data.id) return data;
    } catch (err) {
      console.warn(`[hospitalService] FastAPI /hospitals/${id} unavailable, falling back to LocalDB:`, err);
    }
    return db.getHospitals().find(h => h.id === id);
  },

  recommendHospitals: async (
    filter: 'CARE_SCORE' | 'LOWEST_COST' | 'NEAREST' = 'CARE_SCORE',
    patientId: string = 'usr-patient-1'
  ): Promise<Hospital[]> => {
    try {
      const profile = db.getPatientProfile();
      const response = await apiClient.post<{ hospitals?: Hospital[]; recommendations?: any[] }>('/hospitals/recommend', {
        patient_id: patientId,
        budget_preference: profile.financialBudgetPreference || 'MEDIUM',
        specialty: 'Cardiology'
      });
      if (response && Array.isArray(response.hospitals) && response.hospitals.length > 0) {
        let list = response.hospitals;
        if (filter === 'LOWEST_COST') {
          list = [...list].sort((a, b) => a.estimatedCostRange.min - b.estimatedCostRange.min);
        } else if (filter === 'NEAREST') {
          list = [...list].sort((a, b) => a.distanceKm - b.distanceKm);
        } else {
          list = [...list].sort((a, b) => (b.chikitsaxCareScore || b.care_score || 0) - (a.chikitsaxCareScore || a.care_score || 0));
        }
        return list;
      }
    } catch (err) {
      console.warn('[hospitalService] FastAPI recommendation failed, falling back to LocalDB:', err);
    }
    return mockHospitalService.getRankedHospitals(filter);
  },

  getHospitalReviews: async (hospitalId: string): Promise<any[]> => {
    try {
      const res = await apiClient.get<any[]>(`/hospitals/${hospitalId}/reviews`);
      if (Array.isArray(res)) return res;
    } catch (err) {
      console.warn(`[hospitalService] getHospitalReviews failed for ${hospitalId}:`, err);
    }
    return [];
  },

  submitHospitalReview: async (hospitalId: string, rating: number, reviewText: string): Promise<any> => {
    return apiClient.post<any>(`/hospitals/${hospitalId}/reviews`, {
      rating,
      review_text: reviewText
    });
  }
};

export const doctorService = {
  getDoctors: async (hospitalId?: string): Promise<Doctor[]> => {
    try {
      const endpoint = hospitalId ? `/doctors?hospital_id=${hospitalId}` : '/doctors';
      const data = await apiClient.get<Doctor[]>(endpoint);
      if (Array.isArray(data) && data.length > 0) return data;
    } catch (err) {
      console.warn('[doctorService] FastAPI /doctors endpoint unavailable, falling back to LocalDB:', err);
    }
    return db.getDoctors();
  },

  getDoctorById: async (doctorId: string): Promise<Doctor | undefined> => {
    try {
      const data = await apiClient.get<Doctor>(`/doctors/${doctorId}`);
      if (data && data.id) return data;
    } catch (err) {
      console.warn(`[doctorService] FastAPI /doctors/${doctorId} unavailable, falling back to LocalDB:`, err);
    }
    return db.getDoctors().find(d => d.id === doctorId);
  },

  getDoctorSchedule: async (doctorId?: string): Promise<{
    doctorId: string;
    doctorName: string;
    weeklySchedule: DoctorScheduleItem[];
    blockedSlots: (BlockedSlotInfo | string)[];
    availableDays: string[];
    availableSlots: string[];
  }> => {
    const endpoint = doctorId ? `/doctors/${doctorId}/schedule` : '/doctors/me/schedule';
    const res = await apiClient.get<any>(endpoint);
    return {
      doctorId: res.doctorId || res.doctor_id || doctorId || '',
      doctorName: res.doctorName || res.doctor_name || '',
      weeklySchedule: res.weeklySchedule || res.weekly_schedule || [],
      blockedSlots: res.blockedSlots || res.blocked_slots || [],
      availableDays: res.availableDays || res.available_days || [],
      availableSlots: res.availableSlots || res.available_slots || []
    };
  },

  updateDoctorSchedule: async (
    weeklySchedule: DoctorScheduleItem[],
    doctorId?: string
  ): Promise<{
    weeklySchedule: DoctorScheduleItem[];
    blockedSlots: (BlockedSlotInfo | string)[];
  }> => {
    const endpoint = doctorId ? `/doctors/${doctorId}/schedule` : '/doctors/me/schedule';
    const res = await apiClient.put<any>(endpoint, {
      weeklySchedule,
      weekly_schedule: weeklySchedule
    });
    return {
      weeklySchedule: res.weeklySchedule || res.weekly_schedule || weeklySchedule,
      blockedSlots: res.blockedSlots || res.blocked_slots || []
    };
  },

  blockSlot: async (
    slotData: { date?: string; time?: string; day?: string; slot?: string; reason?: string },
    doctorId?: string
  ): Promise<{
    weeklySchedule: DoctorScheduleItem[];
    blockedSlots: (BlockedSlotInfo | string)[];
  }> => {
    const endpoint = doctorId ? `/doctors/${doctorId}/block-slot` : '/doctors/me/block-slot';
    const res = await apiClient.post<any>(endpoint, slotData);
    return {
      weeklySchedule: res.weeklySchedule || res.weekly_schedule || [],
      blockedSlots: res.blockedSlots || res.blocked_slots || []
    };
  },

  unblockSlot: async (
    slotData: { date?: string; time?: string; day?: string; slot?: string },
    doctorId?: string
  ): Promise<{
    weeklySchedule: DoctorScheduleItem[];
    blockedSlots: (BlockedSlotInfo | string)[];
  }> => {
    const endpoint = doctorId ? `/doctors/${doctorId}/unblock-slot` : '/doctors/me/unblock-slot';
    const res = await apiClient.post<any>(endpoint, slotData);
    return {
      weeklySchedule: res.weeklySchedule || res.weekly_schedule || [],
      blockedSlots: res.blockedSlots || res.blocked_slots || []
    };
  },

  getDoctorAvailability: async (doctorId: string, date: string): Promise<DoctorAvailability> => {
    const res = await apiClient.get<any>(`/doctors/${doctorId}/availability?date=${encodeURIComponent(date)}`);
    return {
      doctorId: res.doctorId || res.doctor_id || doctorId,
      date: res.date || date,
      day: res.day,
      isDayBlocked: Boolean(res.isDayBlocked ?? res.is_day_blocked),
      slots: Array.isArray(res.slots) ? res.slots.map((s: any) => ({
        time: s.time,
        isAvailable: Boolean(s.isAvailable ?? s.is_available),
        isBlocked: Boolean(s.isBlocked ?? s.is_blocked),
        isBooked: Boolean(s.isBooked ?? s.is_booked)
      })) : []
    };
  }
};

export const opdService = {
  bookAppointment: async (
    hospitalId: string,
    hospitalName: string,
    department: string,
    doctorId: string,
    doctorName: string,
    appointmentDate: string,
    appointmentTime: string
  ): Promise<OPDRegistration> => {
    const currentUser = db.getCurrentUser();
    const patientId = currentUser?.id || 'usr-patient-1';

    const payload = {
      patient_id: patientId,
      hospital_id: hospitalId,
      doctor_id: doctorId,
      department,
      appointment_date: appointmentDate,
      appointment_time: appointmentTime,
      date: appointmentDate,
      time: appointmentTime
    };

    const res = await apiClient.post<any>('/opd', payload);
    if (res && res.reference_id) {
      const opdRecord: OPDRegistration = {
        id: res.id || res.appointment_id || `opd-${Date.now()}`,
        referenceId: res.reference_id,
        patientId: res.patient_id || patientId,
        patientName: res.patient_name || currentUser?.name || 'Ramesh Sharma',
        patientPhone: res.patient_phone || '+91 98765 43210',
        hospitalId,
        hospitalName: res.hospital_name || res.hospital || hospitalName,
        department,
        doctorId,
        doctorName: res.doctor_name || res.doctor || doctorName,
        appointmentDate: res.appointment_date || appointmentDate,
        appointmentTime: res.appointment_time || appointmentTime,
        consultationFee: res.consultation_fee || 800,
        status: (res.status || 'CONFIRMED').toUpperCase() as any,
        createdAt: new Date().toLocaleDateString('en-IN'),
        qrToken: res.qr_token || `TOKEN_SECURE_${res.reference_id}_${Date.now()}`
      };
      // Keep local store synchronized as cache
      db.createOPDRegistration(opdRecord);
      return opdRecord;
    }
    throw new Error('Failed to book appointment: Server returned an invalid response.');
  },

  getAppointmentByRef: async (referenceId: string): Promise<OPDRegistration | null> => {
    try {
      const res = await apiClient.get<any>(`/opd/reference/${encodeURIComponent(referenceId)}`);
      if (res && res.reference_id) {
        return {
          id: res.id || res.appointment_id,
          referenceId: res.reference_id,
          patientId: res.patient_id || 'usr-patient-1',
          patientName: res.patient_name || 'Ramesh Sharma',
          patientPhone: res.patient_phone || '+91 98765 43210',
          hospitalId: res.hospital_id || 'hosp-1',
          hospitalName: res.hospital_name || res.hospital || 'CarePlus Super Specialty Hospital',
          department: res.department,
          doctorId: res.doctor_id || 'doc-1',
          doctorName: res.doctor_name || res.doctor || 'Dr. Rajesh Kulkarni',
          appointmentDate: res.appointment_date,
          appointmentTime: res.appointment_time,
          consultationFee: res.consultation_fee || 800,
          status: (res.status || 'CONFIRMED').toUpperCase() as any,
          createdAt: new Date().toLocaleDateString('en-IN'),
          qrToken: res.qr_token || `TOKEN_SECURE_${res.reference_id}`
        };
      }
    } catch (err) {
      console.warn(`[opdService] Backend /api/opd/reference/${referenceId} failed:`, err);
    }
    return null;
  },

  getAppointments: async (
    filters?: string | { patientId?: string; doctorId?: string; hospitalId?: string; status?: string }
  ): Promise<OPDRegistration[]> => {
    try {
      const params = new URLSearchParams();
      if (typeof filters === 'string') {
        if (filters.trim()) params.append('patient_id', filters.trim());
      } else if (filters && typeof filters === 'object') {
        if (filters.patientId) params.append('patient_id', filters.patientId);
        if (filters.doctorId) params.append('doctor_id', filters.doctorId);
        if (filters.hospitalId) params.append('hospital_id', filters.hospitalId);
        if (filters.status) params.append('status', filters.status);
      }

      const queryString = params.toString() ? `?${params.toString()}` : '';
      const res = await apiClient.get<any[]>(`/opd${queryString}`);
      if (Array.isArray(res)) {
        return res.map(r => ({
          id: r.id || r.appointment_id,
          referenceId: r.reference_id,
          patientId: r.patient_id || 'usr-patient-1',
          patientName: r.patient_name || 'Ramesh Sharma',
          patientPhone: r.patient_phone || '+91 98765 43210',
          hospitalId: r.hospital_id || 'hosp-1',
          hospitalName: r.hospital_name || r.hospital || 'CarePlus Super Specialty Hospital',
          department: r.department,
          doctorId: r.doctor_id || 'doc-1',
          doctorName: r.doctor_name || r.doctor || 'Dr. Rajesh Kulkarni',
          appointmentDate: r.appointment_date,
          appointmentTime: r.appointment_time,
          consultationFee: r.consultation_fee || 800,
          status: (r.status || 'CONFIRMED').toUpperCase() as any,
          createdAt: new Date().toLocaleDateString('en-IN'),
          qrToken: r.qr_token || `TOKEN_SECURE_${r.reference_id}`
        }));
      }
      return [];
    } catch (err) {
      console.error('[opdService] Backend list appointments failed:', err);
      throw err;
    }
  },

  cancelAppointment: async (appointmentId: string): Promise<boolean> => {
    await apiClient.put<any>(`/opd/${appointmentId}/cancel`);
    db.updateOPDStatus(appointmentId, 'CANCELLED');
    return true;
  },

  rescheduleAppointment: async (appointmentId: string, newDate: string, newTime: string): Promise<boolean> => {
    await apiClient.put<any>(`/opd/${appointmentId}/reschedule`, {
      appointment_date: newDate,
      appointment_time: newTime
    });
    db.rescheduleOPD(appointmentId, newDate, newTime);
    return true;
  }
};

export const qrService = {
  generateQR: async (appointmentId: string): Promise<{ reference_id: string; secure_token: string; qr_payload: string }> => {
    try {
      const res = await apiClient.post<any>('/qr', { appointment_id: appointmentId });
      if (res && res.reference_id) {
        return {
          reference_id: res.reference_id,
          secure_token: res.secure_token || res.token,
          qr_payload: res.qr_payload || `CHIKITSAX_SECURE_PASS:${res.reference_id}:${res.secure_token || res.token}`
        };
      }
    } catch (err) {
      console.warn('[qrService] Backend /api/qr failed, falling back to LocalDB format:', err);
    }
    const local = db.getOPDRegistrations().find(o => o.id === appointmentId || o.referenceId === appointmentId);
    const ref = local ? local.referenceId : appointmentId;
    const tok = local ? local.qrToken : `TOKEN_SECURE_${ref}`;
    return {
      reference_id: ref,
      secure_token: tok,
      qr_payload: `CHIKITSAX_SECURE_PASS:${ref}:${tok}`
    };
  },

  verifyPass: async (referenceId: string, staffName: string = 'Reception Desk Staff'): Promise<{ success: boolean; opd?: OPDRegistration; message: string }> => {
    try {
      const res = await apiClient.post<any>('/hospital/verify', { reference_id: referenceId, staff_name: staffName });
      if (res) {
        const isSuccess = Boolean(res.verified);
        let opdRecord: OPDRegistration | undefined = undefined;
        if (res.appointment) {
          opdRecord = {
            id: res.appointment.id || `opd-${res.reference_id}`,
            referenceId: res.reference_id || referenceId,
            patientId: res.appointment.patientId || 'usr-patient-1',
            patientName: res.appointment.patientName || 'Patient',
            patientPhone: res.appointment.patientPhone || '',
            hospitalId: res.appointment.hospitalId || 'hosp-1',
            hospitalName: res.appointment.hospitalName || res.hospital || 'Hospital',
            department: res.appointment.department || res.department || 'General Medicine',
            doctorId: res.appointment.doctorId || 'doc-1',
            doctorName: res.appointment.doctorName || res.doctor || 'Doctor',
            appointmentDate: res.appointment.appointmentDate || res.appointment_date || 'Today',
            appointmentTime: res.appointment.appointmentTime || res.appointment_time || '11:30 AM',
            consultationFee: 800,
            status: res.appointment.status || (isSuccess ? 'VERIFIED' : 'CONFIRMED'),
            createdAt: new Date().toLocaleDateString('en-IN'),
            qrToken: `TOKEN_SECURE_${res.reference_id}`
          };
          db.createOPDRegistration(opdRecord);
        }
        return {
          success: isSuccess,
          opd: opdRecord,
          message: res.message || (isSuccess ? 'Verification successful' : 'Verification failed')
        };
      }
    } catch (err: any) {
      return {
        success: false,
        message: err?.message || 'Verification failed on server.'
      };
    }
    return db.verifyQRPass(referenceId, staffName);
  }
};

/**
 * 1. AI Voice Intake API Service
 */
export const voiceService = {
  processVoiceTranscript: async (transcriptText: string, patientId?: string): Promise<SymptomIntake> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const response = await apiClient.post<any>('/intake', {
        patient_id: pid,
        transcript: transcriptText,
        language: 'en-IN'
      });
      if (response && (response.id || response.intake_id)) {
        const intakeId = response.id || response.intake_id;
        const intake: SymptomIntake = {
          id: intakeId,
          patientId: response.patient_id || response.patientId || pid,
          timestamp: response.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          rawTranscript: response.raw_transcript || response.rawTranscript || transcriptText,
          extractedSymptoms: response.extracted_symptoms || response.extractedSymptoms || [],
          duration: response.duration || '24 Hours',
          severity: response.severity || 'Moderate',
          affectedBodyPart: response.affected_body_part || response.affectedBodyPart || 'General',
          isEmergencyAlert: Boolean(response.is_emergency_alert ?? response.isEmergencyAlert)
        };
        db.addSymptomIntake(intake);
        return intake;
      }
      throw new Error('Invalid response received from intake service.');
    } catch (err) {
      console.error('[voiceService] /api/intake failed:', err);
      throw err;
    }
  },

  getIntakes: async (patientId?: string): Promise<SymptomIntake[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/intake/patient/${pid}`);
      if (Array.isArray(res)) {
        return res.map(r => ({
          id: r.id,
          patientId: r.patient_id || r.patientId || pid,
          timestamp: r.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          rawTranscript: r.raw_transcript || r.rawTranscript || '',
          extractedSymptoms: r.extracted_symptoms || r.extractedSymptoms || [],
          duration: r.duration || 'Recent',
          severity: r.severity || 'Moderate',
          affectedBodyPart: r.affected_body_part || r.affectedBodyPart || 'General',
          isEmergencyAlert: Boolean(r.is_emergency_alert ?? r.isEmergencyAlert)
        }));
      }
      return [];
    } catch (err) {
      console.warn('[voiceService] getIntakes failed:', err);
      throw err;
    }
  }
};

export const mockVoiceService = {
  processVoiceTranscript: async (transcriptText: string): Promise<SymptomIntake> => {
    const lower = transcriptText.toLowerCase();
    const symptoms: string[] = [];

    if (lower.includes('chest') || lower.includes('discomfort') || lower.includes('pressure')) symptoms.push('Chest Discomfort');
    if (lower.includes('breath') || lower.includes('breathing') || lower.includes('shortness')) symptoms.push('Shortness of Breath');
    if (lower.includes('fatigue') || lower.includes('tired') || lower.includes('weak')) symptoms.push('Fatigue');
    if (lower.includes('headache') || lower.includes('head') || lower.includes('migraine')) symptoms.push('Headache');
    if (lower.includes('dizzy') || lower.includes('dizziness')) symptoms.push('Dizziness');
    if (lower.includes('fever') || lower.includes('temperature') || lower.includes('chills')) symptoms.push('Fever');
    if (lower.includes('throat') || lower.includes('sore') || lower.includes('swallow')) symptoms.push('Sore Throat');
    if (lower.includes('cough') || lower.includes('cold') || lower.includes('sneeze')) symptoms.push('Cough & Cold');
    if (lower.includes('stomach') || lower.includes('abdominal') || lower.includes('nausea') || lower.includes('vomit') || lower.includes('belly')) symptoms.push('Abdominal Discomfort');
    if (lower.includes('back') || lower.includes('joint') || lower.includes('muscle') || lower.includes('leg')) symptoms.push('Joint / Muscle Pain');

    if (symptoms.length === 0) {
      symptoms.push(`Symptom: ${transcriptText.trim().substring(0, 35)}`);
    }

    let severity: 'Mild' | 'Moderate' | 'Severe' | 'Critical' = 'Moderate';
    let isEmergency = false;

    if (lower.includes('severe') || lower.includes('intense') || lower.includes('radiating') || lower.includes('unbearable') || lower.includes('critical')) {
      severity = 'Severe';
      if (lower.includes('chest') || lower.includes('breath') || lower.includes('heart')) {
        isEmergency = true;
      }
    } else if (lower.includes('mild') || lower.includes('slight') || lower.includes('minor')) {
      severity = 'Mild';
    }

    let bodySystem = 'General / Constitutional';
    if (symptoms.some(s => s.includes('Chest') || s.includes('Breath'))) bodySystem = 'Cardiovascular / Thoracic';
    else if (symptoms.some(s => s.includes('Throat') || s.includes('Cough'))) bodySystem = 'Respiratory / ENT';
    else if (symptoms.some(s => s.includes('Abdominal'))) bodySystem = 'Gastrointestinal';
    else if (symptoms.some(s => s.includes('Headache') || s.includes('Dizziness'))) bodySystem = 'Neurological';

    let duration = '12 Hours';
    if (lower.includes('yesterday')) duration = '24 Hours';
    else if (lower.includes('2 days') || lower.includes('two days')) duration = '2 Days';
    else if (lower.includes('3 days') || lower.includes('three days')) duration = '3 Days';
    else if (lower.includes('week')) duration = '1 Week';

    const intake: SymptomIntake = {
      id: `intake-${Date.now()}`,
      patientId: db.getPatientProfile().userId,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      rawTranscript: transcriptText,
      extractedSymptoms: symptoms,
      duration,
      severity,
      affectedBodyPart: bodySystem,
      isEmergencyAlert: isEmergency
    };

    db.addSymptomIntake(intake);
    return intake;
  }
};

/**
 * 2. Medical Record Service (Upload, List, File Download)
 */
export const recordService = {
  getRecords: async (patientId?: string): Promise<MedicalRecord[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/medical-records/${pid}`);
      if (Array.isArray(res)) {
        return res.map(r => ({
          id: r.id,
          patientId: r.patient_id || r.patientId,
          fileName: r.file_name || r.fileName,
          fileType: (r.file_type || r.fileType || 'PDF').toUpperCase() as any,
          category: r.category,
          uploadDate: r.upload_date || r.uploadDate,
          ocrExtractedData: r.ocr_extracted_data || r.ocrExtractedData || {},
          isVerifiedByPatient: Boolean(r.is_verified_by_patient ?? r.isVerifiedByPatient ?? true)
        }));
      }
      return [];
    } catch (err) {
      console.warn('[recordService] getRecords error:', err);
      throw err;
    }
  },

  uploadRecord: async (
    fileName: string,
    fileType: 'PDF' | 'JPG' | 'PNG',
    category: 'Prescription' | 'Lab Report' | 'Discharge Summary' | 'Radiology Report' | 'Other',
    fileObject?: File,
    patientId?: string
  ): Promise<MedicalRecord> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    let res: any;
    if (fileObject && fileObject.size > 0 && typeof FormData !== 'undefined') {
      const formData = new FormData();
      formData.append('patient_id', pid);
      formData.append('category', category);
      formData.append('file', fileObject, fileName);
      res = await apiClient.postFormData<any>('/medical-records/upload', formData);
    } else {
      res = await apiClient.post<any>('/medical-records', {
        patient_id: pid,
        file_name: fileName,
        file_type: fileType,
        category: category
      });
    }

    if (res && (res.id || res.record_id)) {
      const recId = res.id || res.record_id;
      const record: MedicalRecord = {
        id: recId,
        patientId: res.patient_id || pid,
        fileName: res.file_name || fileName,
        fileType: (res.file_type || fileType).toUpperCase() as any,
        category: res.category || category,
        uploadDate: res.upload_date || new Date().toLocaleDateString('en-IN'),
        ocrExtractedData: res.ocr_extracted_data || res.extracted_fields || {},
        isVerifiedByPatient: Boolean(res.is_verified_by_patient ?? true)
      };
      db.addMedicalRecord(record);
      return record;
    }
    throw new Error('Failed to upload medical record: server returned invalid response.');
  },

  downloadRecordFile: async (recordId: string, fileName?: string): Promise<void> => {
    const blob = await apiClient.getBlob(`/medical-records/file/${recordId}`);
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = fileName || `medical_record_${recordId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
  },

  downloadRecordFileUrl: (recordId: string): string => {
    const baseUrl = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api';
    return `${baseUrl}/medical-records/file/${recordId}`;
  }
};

/**
 * 2B. Medical Record OCR Upload API Service (Delegates to recordService)
 */
export const ocrService = {
  processUploadedFile: async (
    fileName: string,
    fileType: 'PDF' | 'JPG' | 'PNG',
    category: 'Prescription' | 'Lab Report' | 'Discharge Summary' | 'Radiology Report' | 'Other',
    fileObject?: File,
    patientId?: string
  ): Promise<MedicalRecord> => {
    return recordService.uploadRecord(fileName, fileType, category, fileObject, patientId);
  }
};

/**
 * 2C. Patient Access Consent Service
 */
export const consentService = {
  getConsents: async (patientId?: string): Promise<PatientConsent[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/consent/${pid}`);
      if (Array.isArray(res)) {
        return res.map(c => ({
          id: c.id,
          patientId: c.patientId || c.patient_id,
          hospitalId: c.hospitalId || c.hospital_id,
          hospitalName: c.hospitalName || c.hospital_name,
          doctorId: c.doctorId || c.doctor_id,
          doctorName: c.doctorName || c.doctor_name,
          requestedAt: c.requestedAt || new Date().toISOString(),
          grantedAt: c.grantedAt,
          status: c.status,
          accessibleSections: c.accessibleSections || c.accessible_sections || ['PROFILE', 'SYMPTOMS', 'OCR_RECORDS']
        }));
      }
      return [];
    } catch (err) {
      console.warn('[consentService] getConsents error:', err);
      throw err;
    }
  },

  grantConsent: async (payload: {
    patientId?: string;
    hospitalId: string;
    hospitalName: string;
    doctorId?: string;
    doctorName?: string;
    granted?: boolean;
  }): Promise<PatientConsent> => {
    const user = db.getCurrentUser();
    const body = {
      patient_id: payload.patientId || user?.id || 'me',
      hospital_id: payload.hospitalId,
      hospital_name: payload.hospitalName,
      doctor_id: payload.doctorId,
      doctor_name: payload.doctorName,
      granted: payload.granted !== undefined ? payload.granted : true
    };
    const res = await apiClient.post<any>('/consent', body);
    const consent: PatientConsent = {
      id: res.id,
      patientId: res.patientId || res.patient_id || body.patient_id,
      hospitalId: res.hospitalId || res.hospital_id || body.hospital_id,
      hospitalName: res.hospitalName || res.hospital_name || body.hospital_name,
      doctorId: res.doctorId || res.doctor_id,
      doctorName: res.doctorName || res.doctor_name,
      requestedAt: res.requestedAt || new Date().toISOString(),
      grantedAt: res.grantedAt || (res.status === 'GRANTED' ? new Date().toISOString() : undefined),
      status: res.status || 'GRANTED',
      accessibleSections: res.accessibleSections || res.accessible_sections || ['PROFILE', 'SYMPTOMS', 'OCR_RECORDS']
    };
    if (consent.status === 'GRANTED' || consent.status === 'REVOKED') {
      db.updateConsentStatus(consent.id, consent.status);
    }
    return consent;
  },

  revokeConsent: async (consentId: string): Promise<PatientConsent> => {
    const res = await apiClient.put<any>(`/consent/${consentId}/revoke`);
    db.updateConsentStatus(consentId, 'REVOKED');
    return {
      id: res.id,
      patientId: res.patientId || res.patient_id,
      hospitalId: res.hospitalId || res.hospital_id,
      hospitalName: res.hospitalName || res.hospital_name,
      doctorId: res.doctorId || res.doctor_id,
      doctorName: res.doctorName || res.doctor_name,
      requestedAt: res.requestedAt || new Date().toISOString(),
      status: 'REVOKED',
      accessibleSections: res.accessibleSections || []
    };
  }
};

/**
 * 2D. Doctor Consultation Service
 */
export const consultationService = {
  getConsultation: async (appointmentId: string): Promise<Consultation | null> => {
    try {
      const res = await apiClient.get<any>(`/consultations/${appointmentId}`);
      if (res && res.id) {
        return {
          id: res.id,
          appointmentId: res.appointmentId || appointmentId,
          referenceId: res.referenceId || '',
          patientId: res.patientId || '',
          patientName: res.patientName || '',
          doctorId: res.doctorId || '',
          doctorName: res.doctorName || '',
          hospitalId: res.hospitalId || '',
          timestamp: res.timestamp || new Date().toLocaleString('en-IN'),
          clinicalNotes: res.clinicalNotes || '',
          diagnosis: res.diagnosis || '',
          investigationsOrdered: res.investigationsOrdered || [],
          prescriptionMedicines: res.prescriptionMedicines || [],
          treatmentPlan: res.treatmentPlan || '',
          status: res.status || 'COMPLETED'
        };
      }
    } catch (err: any) {
      console.warn('[consultationService] Failed to fetch consultation from backend:', err?.message || err);
    }
    return null;
  },

  finalizeConsultation: async (payload: {
    appointmentId: string;
    patientId?: string;
    clinicalNotes: string;
    diagnosis: string;
    investigationsOrdered?: string[];
    prescriptionMedicines?: { name: string; dosage: string; duration: string }[];
    treatmentPlan: string;
    estimatedCost?: number;
  }): Promise<Consultation> => {
    const res = await apiClient.post<any>('/consultations', {
      appointmentId: payload.appointmentId,
      appointment_id: payload.appointmentId,
      patientId: payload.patientId,
      patient_id: payload.patientId,
      clinicalNotes: payload.clinicalNotes,
      clinical_notes: payload.clinicalNotes,
      diagnosis: payload.diagnosis,
      investigationsOrdered: payload.investigationsOrdered || [],
      investigations_ordered: payload.investigationsOrdered || [],
      prescriptionMedicines: payload.prescriptionMedicines || [],
      prescription_medicines: payload.prescriptionMedicines || [],
      treatmentPlan: payload.treatmentPlan,
      treatment_plan: payload.treatmentPlan,
      estimated_cost: payload.estimatedCost
    });

    const consultation: Consultation = {
      id: res.id,
      appointmentId: res.appointmentId || payload.appointmentId,
      referenceId: res.referenceId || '',
      patientId: res.patientId || payload.patientId || '',
      patientName: res.patientName || '',
      doctorId: res.doctorId || '',
      doctorName: res.doctorName || '',
      hospitalId: res.hospitalId || '',
      timestamp: new Date().toLocaleString('en-IN'),
      clinicalNotes: res.clinicalNotes || payload.clinicalNotes,
      diagnosis: res.diagnosis || payload.diagnosis,
      investigationsOrdered: res.investigationsOrdered || payload.investigationsOrdered || [],
      prescriptionMedicines: res.prescriptionMedicines || payload.prescriptionMedicines || [],
      treatmentPlan: res.treatmentPlan || payload.treatmentPlan,
      status: 'COMPLETED'
    };

    // Keep LocalDB synced as well
    try {
      db.addConsultation(consultation);
    } catch {
      // ignore
    }

    return consultation;
  },

  saveDraft: async (payload: {
    appointmentId: string;
    clinicalNotes?: string;
    diagnosis?: string;
    investigationsOrdered?: string[];
    prescriptionMedicines?: { name: string; dosage: string; duration: string }[];
    treatmentPlan?: string;
  }): Promise<any> => {
    return apiClient.post<any>('/consultations/draft', {
      appointmentId: payload.appointmentId,
      appointment_id: payload.appointmentId,
      clinicalNotes: payload.clinicalNotes,
      clinical_notes: payload.clinicalNotes,
      diagnosis: payload.diagnosis,
      investigationsOrdered: payload.investigationsOrdered,
      investigations_ordered: payload.investigationsOrdered,
      prescriptionMedicines: payload.prescriptionMedicines,
      prescription_medicines: payload.prescriptionMedicines,
      treatmentPlan: payload.treatmentPlan,
      treatment_plan: payload.treatmentPlan
    });
  },

  getDraft: async (appointmentId: string): Promise<any | null> => {
    try {
      return await apiClient.get<any>(`/consultations/draft/${appointmentId}`);
    } catch (err: any) {
      if (err?.status === 404) return null;
      throw err;
    }
  }
};

export const mockOCRService = {
  processUploadedFile: async (
    fileName: string,
    fileType: 'PDF' | 'JPG' | 'PNG',
    category: 'Prescription' | 'Lab Report' | 'Discharge Summary' | 'Radiology Report' | 'Other'
  ): Promise<MedicalRecord> => {
    // Phase 5.3: Delegate directly to authentic recordService rather than simulating fake data
    return recordService.uploadRecord(fileName, fileType, category);
  }
};

/**
 * 3. AI Triage Engine Service
 */
export const triageService = {
  runClinicalTriage: async (patientId?: string, intakeId?: string): Promise<TriageResult> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const payload: any = { patient_id: pid };
      if (intakeId) {
        payload.intake_id = intakeId;
      }
      const response = await apiClient.post<any>('/triage', payload);
      if (response && (response.id || response.patient_id)) {
        const triage: TriageResult = {
          id: response.id || `tri-${Date.now()}`,
          patientId: response.patient_id || response.patientId || pid,
          timestamp: response.timestamp || new Date().toLocaleString('en-IN'),
          riskLevel: (response.risk_level || response.riskLevel || 'MODERATE').toUpperCase() as any,
          urgency: response.urgency || 'Prompt Consultation (24h)',
          symptomsConsidered: response.symptoms_considered || response.symptomsConsidered || [],
          clinicalReasoning: response.reasoning || response.clinical_reasoning || response.clinicalReasoning || [],
          recommendedSpecialty: Array.isArray(response.recommended_specialties)
            ? response.recommended_specialties.join(' / ')
            : response.recommended_specialty || response.recommendedSpecialty || 'General Medicine',
          recommendedNextStep: response.next_action || response.recommended_next_step || response.recommendedNextStep || 'Consult Outpatient OPD',
          isEmergencyTriggered: Boolean(response.is_emergency_triggered ?? response.isEmergencyTriggered ?? (response.risk_level === 'HIGH'))
        };
        db.saveTriageResult(triage);
        return triage;
      }
      throw new Error('Invalid response received from triage service.');
    } catch (err) {
      console.error('[triageService] /api/triage failed:', err);
      throw err;
    }
  },

  getTriageResults: async (patientId?: string): Promise<TriageResult[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/triage/patient/${pid}`);
      if (Array.isArray(res)) {
        return res.map(response => ({
          id: response.id,
          patientId: response.patient_id || response.patientId || pid,
          timestamp: response.timestamp || new Date().toLocaleString('en-IN'),
          riskLevel: (response.risk_level || response.riskLevel || 'MODERATE').toUpperCase() as any,
          urgency: response.urgency || 'Prompt Consultation (24h)',
          symptomsConsidered: response.symptoms_considered || response.symptomsConsidered || [],
          clinicalReasoning: response.reasoning || response.clinical_reasoning || response.clinicalReasoning || [],
          recommendedSpecialty: Array.isArray(response.recommended_specialties)
            ? response.recommended_specialties.join(' / ')
            : response.recommended_specialty || response.recommendedSpecialty || 'General Medicine',
          recommendedNextStep: response.next_action || response.recommended_next_step || response.recommendedNextStep || 'Consult Outpatient OPD',
          isEmergencyTriggered: Boolean(response.is_emergency_triggered ?? response.isEmergencyTriggered ?? (response.risk_level === 'HIGH'))
        }));
      }
      return [];
    } catch (err) {
      console.warn('[triageService] getTriageResults failed:', err);
      throw err;
    }
  }
};

export const mockTriageService = {
  runClinicalTriage: async (): Promise<TriageResult> => {
    const profile = db.getPatientProfile();
    const intakes = db.getSymptomIntakes();
    const latestIntake = intakes.length > 0 ? intakes[0] : null;

    const hasChestSymptoms = profile.symptoms.some(s => s.toLowerCase().includes('chest'));
    const hasThroatFever = profile.symptoms.some(s => s.toLowerCase().includes('throat') || s.toLowerCase().includes('fever') || s.toLowerCase().includes('cough'));
    const isSevere = latestIntake?.severity === 'Severe' || latestIntake?.severity === 'Critical';

    let riskLevel: 'LOW' | 'MODERATE' | 'HIGH' = 'MODERATE';
    let urgency: TriageResult['urgency'] = 'Prompt Consultation (24h)';
    let specialty = 'Cardiology & Internal Medicine';
    const reasoning: string[] = [];

    if (hasChestSymptoms && isSevere) {
      riskLevel = 'HIGH';
      urgency = 'Urgent Evaluation (Immediate)';
      specialty = 'Cardiology / Emergency Care';
      reasoning.push('Reported severe chest discomfort / cardiovascular pressure');
      reasoning.push('Recommendation: Seek immediate cardiac evaluation or emergency trauma care');
    } else if (hasChestSymptoms) {
      riskLevel = 'MODERATE';
      urgency = 'Prompt Consultation (24h)';
      specialty = 'Cardiology & Internal Medicine';
      reasoning.push('Cardiovascular chest discomfort noted with moderate duration');
      reasoning.push('Elective Cardiology consultation advised within 24 hours');
    } else if (hasThroatFever) {
      riskLevel = 'LOW';
      urgency = 'Routine Consultation';
      specialty = 'General Medicine / ENT';
      reasoning.push(`Active symptoms evaluated: ${profile.symptoms.join(', ')}`);
      reasoning.push('No acute cardiac red flags detected. Routine Outpatient OPD registration recommended.');
    } else {
      riskLevel = 'LOW';
      urgency = 'Routine Consultation';
      specialty = 'General Outpatient Medicine';
      reasoning.push(`Extracted symptoms evaluated: ${profile.symptoms.join(', ') || 'Mild Malaise'}`);
      reasoning.push('Routine Outpatient OPD booking suitable');
    }

    const triage: TriageResult = {
      id: `tri-${Date.now()}`,
      patientId: profile.userId,
      timestamp: new Date().toLocaleString('en-IN'),
      riskLevel,
      urgency,
      symptomsConsidered: profile.symptoms,
      clinicalReasoning: reasoning,
      recommendedSpecialty: specialty,
      recommendedNextStep: urgency === 'Urgent Evaluation (Immediate)'
        ? 'Proceed to nearest Emergency Trauma center or activate Emergency Pathway'
        : `Compare and select recommended ${specialty} OPD Hospital for registration`,
      isEmergencyTriggered: riskLevel === 'HIGH'
    };

    db.saveTriageResult(triage);
    return triage;
  }
};


/**
 * 4. Smart Hospital Recommendation Engine (CHIKITSAX Care Score)
 */
export const mockHospitalService = {
  getRankedHospitals: (filter?: 'CARE_SCORE' | 'LOWEST_COST' | 'NEAREST'): Hospital[] => {
    const hospitals = db.getHospitals();

    // Calculate CHIKITSAX Care Score formula for each
    const scored = hospitals.map(h => {
      const careScore = Math.round(
        (h.clinicalFitScore * 0.35) +
        (h.affordabilityScore * 0.25) +
        ((100 - (h.distanceKm * 5)) * 0.15) +
        (h.availabilityScore * 0.15) +
        (h.supportServicesScore * 0.10)
      );
      return { ...h, chikitsaxCareScore: Math.min(99, Math.max(70, careScore)) };
    });

    if (filter === 'LOWEST_COST') {
      return scored.sort((a, b) => a.estimatedCostRange.min - b.estimatedCostRange.min);
    } else if (filter === 'NEAREST') {
      return scored.sort((a, b) => a.distanceKm - b.distanceKm);
    }
    // Default: Sort by Care Score
    return scored.sort((a, b) => b.chikitsaxCareScore - a.chikitsaxCareScore);
  },

  getEmergencyHospitals: (): Hospital[] => {
    return db.getHospitals().filter(h => h.emergencyAvailable).sort((a, b) => a.distanceKm - b.distanceKm);
  }
};

/**
 * 5. OPD Registration & Secure QR Service
 */
export const mockOPDService = {
  bookAppointment: async (
    hospitalId: string,
    hospitalName: string,
    department: string,
    doctorId: string,
    doctorName: string,
    appointmentDate: string,
    appointmentTime: string
  ): Promise<OPDRegistration> => {
    await new Promise(r => setTimeout(r, 500));

    const profile = db.getPatientProfile();
    const randomHex = Math.floor(Math.random() * 16777215).toString(16).toUpperCase().padStart(6, '8A92F');
    const referenceId = `CHX-2026-${randomHex}`;
    const qrToken = `TOKEN_SECURE_${referenceId}_${Date.now()}`;

    const opd: OPDRegistration = {
      id: `opd-${Date.now()}`,
      referenceId,
      patientId: profile.userId,
      patientName: profile.fullName,
      patientPhone: profile.phone,
      hospitalId,
      hospitalName,
      department,
      doctorId,
      doctorName,
      appointmentDate,
      appointmentTime,
      consultationFee: 800,
      status: 'CONFIRMED',
      createdAt: new Date().toLocaleDateString('en-IN'),
      qrToken
    };

    db.createOPDRegistration(opd);
    return opd;
  }
};

/**
 * 6. Doctor Consultation & Cost Estimate Service
 */
/**
 * 6. Real Financial & Care-to-Cost Services
 */
export const financeService = {
  createTreatmentEstimate: async (payload: {
    patientId: string;
    hospitalId?: string;
    hospitalName?: string;
    procedureName: string;
    roomCategory?: string;
    estimatedCostMin: number;
    estimatedCostMax: number;
    breakdown?: Record<string, any>;
    consultationId?: string;
  }): Promise<TreatmentCostEstimate> => {
    const res = await apiClient.post<any>('/financial/treatment-estimates', {
      patient_id: payload.patientId,
      patientId: payload.patientId,
      hospital_id: payload.hospitalId || 'hosp-1',
      hospitalId: payload.hospitalId || 'hosp-1',
      hospital_name: payload.hospitalName || 'CarePlus Hospital',
      hospitalName: payload.hospitalName || 'CarePlus Hospital',
      procedure_name: payload.procedureName,
      procedureName: payload.procedureName,
      room_category: payload.roomCategory || 'General Ward',
      roomCategory: payload.roomCategory || 'General Ward',
      estimated_cost_min: payload.estimatedCostMin,
      estimatedCostMin: payload.estimatedCostMin,
      estimated_cost_max: payload.estimatedCostMax,
      estimatedCostMax: payload.estimatedCostMax,
      breakdown: payload.breakdown,
      consultation_id: payload.consultationId,
      consultationId: payload.consultationId
    });

    const est: TreatmentCostEstimate = {
      id: res.id,
      patientId: res.patientId || payload.patientId,
      hospitalId: res.hospitalId || payload.hospitalId || 'hosp-1',
      hospitalName: res.hospitalName || payload.hospitalName || 'CarePlus Hospital',
      procedureName: res.procedureName || payload.procedureName,
      roomCategory: res.roomCategory || payload.roomCategory || 'General Ward',
      estimatedCostRange: res.estimatedCostRange || { min: payload.estimatedCostMin, max: payload.estimatedCostMax },
      breakdown: res.breakdown || payload.breakdown || {},
      confidenceLevel: res.confidenceLevel || 'MEDIUM',
      createdAt: res.createdAt ? new Date(res.createdAt).toLocaleDateString('en-IN') : new Date().toLocaleDateString('en-IN')
    };

    try {
      db.saveCostEstimate(est);
    } catch {
      // ignore
    }
    return est;
  },

  getTreatmentEstimatesForPatient: async (patientId?: string): Promise<TreatmentCostEstimate[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/financial/treatment-estimates/patient/${pid}`);
      if (Array.isArray(res)) {
        return res.map(r => ({
          id: r.id,
          patientId: r.patientId || pid,
          hospitalId: r.hospitalId || 'hosp-1',
          hospitalName: r.hospitalName || 'CarePlus Hospital',
          procedureName: r.procedureName,
          roomCategory: r.roomCategory || 'General Ward',
          estimatedCostRange: r.estimatedCostRange || { min: 0, max: 0 },
          breakdown: r.breakdown || {},
          confidenceLevel: r.confidenceLevel || 'MEDIUM',
          createdAt: r.createdAt ? new Date(r.createdAt).toLocaleDateString('en-IN') : new Date().toLocaleDateString('en-IN')
        }));
      }
    } catch (err: any) {
      console.warn('[financeService] getTreatmentEstimatesForPatient error:', err?.message || err);
      throw err;
    }
    return [];
  },

  assessCareToCost: async (payload: {
    patientId?: string;
    treatmentCost: number;
    hospitalName?: string;
    insuranceCoverage?: number;
    governmentSupport?: number;
    ngoAssistance?: number;
    patientSelfContribution?: number;
    hasInsurance?: boolean;
    hasGovernmentCard?: boolean;
    rationCardType?: string;
  }): Promise<CareToCostAssessment> => {
    const user = db.getCurrentUser();
    const pid = payload.patientId || user?.id || 'me';
    try {
      const res = await apiClient.post<any>('/financial/assess', {
        patient_id: pid,
        patientId: pid,
        treatment_cost: payload.treatmentCost,
        treatmentCost: payload.treatmentCost,
        hospital_name: payload.hospitalName || 'CarePlus Super Specialty Hospital',
        hospitalName: payload.hospitalName || 'CarePlus Super Specialty Hospital',
        insurance_coverage: payload.insuranceCoverage,
        insuranceCoverage: payload.insuranceCoverage,
        government_support: payload.governmentSupport,
        governmentSupport: payload.governmentSupport,
        ngo_assistance: payload.ngoAssistance,
        ngoAssistance: payload.ngoAssistance,
        patient_self_contribution: payload.patientSelfContribution,
        patientSelfContribution: payload.patientSelfContribution,
        has_insurance: payload.hasInsurance,
        has_government_card: payload.hasGovernmentCard,
        ration_card_type: payload.rationCardType
      });

      const assessment: CareToCostAssessment = {
        id: res.id || `ctc-${Date.now()}`,
        patientId: res.patientId || res.patient_id || pid,
        hospitalName: res.hospitalName || res.hospital_name || payload.hospitalName || 'CarePlus Super Specialty Hospital',
        estimatedTreatmentCost: res.estimatedTreatmentCost ?? res.estimated_treatment_cost ?? payload.treatmentCost,
        insuranceCoverage: res.insuranceCoverage ?? res.insurance_support ?? (payload.insuranceCoverage || 0),
        governmentSupport: res.governmentSupport ?? res.government_support ?? (payload.governmentSupport || 0),
        ngoAssistance: res.ngoAssistance ?? res.ngo_support ?? (payload.ngoAssistance || 0),
        patientSelfContribution: res.patientSelfContribution ?? res.patient_self_contribution ?? (payload.patientSelfContribution || 0),
        financialGap: res.financialGap ?? res.estimated_patient_gap ?? 0,
        isFundingComplete: Boolean(res.isFundingComplete ?? res.is_funding_complete ?? false),
        calculatedAt: res.calculatedAt ? new Date(res.calculatedAt).toLocaleString('en-IN') : new Date().toLocaleString('en-IN')
      };

      try {
        db.saveCareToCostAssessment(assessment);
      } catch {
        // ignore
      }
      return assessment;
    } catch (err: any) {
      console.warn('[financeService] assessCareToCost error:', err?.message || err);
      throw err;
    }
  },

  getPatientAssessments: async (patientId?: string): Promise<CareToCostAssessment[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/financial/assessments/patient/${pid}`);
      if (Array.isArray(res)) {
        return res.map(r => ({
          id: r.id,
          patientId: r.patientId || pid,
          hospitalName: r.hospitalName || 'CarePlus Hospital',
          estimatedTreatmentCost: r.estimatedTreatmentCost ?? r.estimated_treatment_cost ?? 0,
          insuranceCoverage: r.insuranceCoverage ?? r.insurance_support ?? 0,
          governmentSupport: r.governmentSupport ?? r.government_support ?? 0,
          ngoAssistance: r.ngoAssistance ?? r.ngo_support ?? 0,
          patientSelfContribution: r.patientSelfContribution ?? r.patient_self_contribution ?? 0,
          financialGap: r.financialGap ?? r.estimated_patient_gap ?? 0,
          isFundingComplete: Boolean(r.isFundingComplete ?? r.is_funding_complete),
          calculatedAt: r.calculatedAt ? new Date(r.calculatedAt).toLocaleString('en-IN') : new Date().toLocaleString('en-IN')
        }));
      }
    } catch (err: any) {
      console.warn('[financeService] getPatientAssessments error:', err?.message || err);
      throw err;
    }
    return [];
  },

  generateFinancePlan: async (payload: {
    patientId?: string;
    treatmentCost: number;
    insuranceCoverage?: number;
    governmentSupport?: number;
    ngoSupport?: number;
    additionalSavings?: number;
  }): Promise<FinanceScenario> => {
    const user = db.getCurrentUser();
    const pid = payload.patientId || user?.id || 'me';
    const res = await apiClient.post<any>('/financial/finance-plan', {
      patient_id: pid,
      patientId: pid,
      treatment_cost: payload.treatmentCost,
      treatmentCost: payload.treatmentCost,
      insurance_coverage: payload.insuranceCoverage || 0,
      insuranceCoverage: payload.insuranceCoverage || 0,
      government_support: payload.governmentSupport || 0,
      governmentSupport: payload.governmentSupport || 0,
      ngo_support: payload.ngoSupport || 0,
      ngoSupport: payload.ngoSupport || 0,
      additional_savings: payload.additionalSavings || 0,
      additionalSavings: payload.additionalSavings || 0
    });

    return {
      id: `plan-${Date.now()}`,
      scenarioTitle: 'Personalized AI Financial Plan',
      hospitalName: 'CarePlus Super Specialty Hospital',
      estimatedCost: res.estimatedCost ?? res.estimated_cost ?? payload.treatmentCost,
      insuranceBenefit: res.insuranceBenefit ?? res.insurance_benefit ?? (payload.insuranceCoverage || 0),
      governmentBenefit: res.governmentBenefit ?? res.government_benefit ?? (payload.governmentSupport || 0),
      ngoBenefit: res.ngoBenefit ?? res.ngo_benefit ?? (payload.ngoSupport || 0),
      patientOutofPocket: res.patientOutOfPocket ?? res.patient_out_of_pocket ?? 0,
      remainingGap: res.remainingGap ?? res.remaining_gap ?? 0,
      recommendationTag: res.recommendationTag ?? res.recommendation_tag ?? 'RECOMMENDED'
    };
  },

  getPatientInsurance: async (patientId?: string): Promise<any[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<any[]>(`/financial/insurance/${pid}`);
      if (Array.isArray(res)) return res;
    } catch (err: any) {
      console.warn('[financeService] getPatientInsurance error:', err?.message || err);
      throw err;
    }
    return [];
  },

  getGovSchemes: async (patientId?: string): Promise<GovernmentScheme[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<GovernmentScheme[]>(`/financial/schemes/${pid}`);
      if (Array.isArray(res)) return res;
    } catch (err: any) {
      console.warn('[financeService] getGovSchemes error:', err?.message || err);
      throw err;
    }
    return [];
  },

  getNGOSupport: async (patientId?: string): Promise<NGOSupport[]> => {
    const user = db.getCurrentUser();
    const pid = patientId || user?.id || 'me';
    try {
      const res = await apiClient.get<NGOSupport[]>(`/financial/ngo-support/${pid}`);
      if (Array.isArray(res)) return res;
    } catch (err: any) {
      console.warn('[financeService] getNGOSupport error:', err?.message || err);
      throw err;
    }
    return [];
  }
};

export const mockDoctorService = {
  createTreatmentCostEstimate: async (
    hospitalId: string,
    hospitalName: string,
    procedureName: string,
    roomCategory: string,
    procedureCost: number,
    roomCharges: number,
    investigationCost: number,
    medicationCost: number,
    otherCharges: number,
    patientId?: string,
    consultationId?: string
  ): Promise<TreatmentCostEstimate> => {
    const totalMin = Math.round((procedureCost + roomCharges + investigationCost + medicationCost + otherCharges) * 0.9);
    const totalMax = Math.round((procedureCost + roomCharges + investigationCost + medicationCost + otherCharges) * 1.15);

    const currentUser = db.getCurrentUser();
    const targetPatientId = patientId || currentUser?.id || 'usr-patient-1';

    return await financeService.createTreatmentEstimate({
      patientId: targetPatientId,
      hospitalId,
      hospitalName,
      procedureName,
      roomCategory,
      estimatedCostMin: totalMin,
      estimatedCostMax: totalMax,
      breakdown: {
        procedureCost,
        roomCharges,
        investigationCost,
        medicationCost,
        otherCharges
      },
      consultationId
    });
  }
};

/**
 * 7. Financial Support & Gap Calculation Service
 */
export const mockFinanceService = {
  checkGovSchemeEligibility: (): SchemeEligibilityResult[] => {
    const profile = db.getPatientProfile();
    const schemes = db.getGovSchemes();

    return schemes.map(s => {
      const isIncomeEligible = Boolean(profile.rationCardType === 'BPL' || profile.incomeCategory?.includes('<'));

      return {
        schemeId: s.id,
        schemeName: s.schemeName,
        isEligible: isIncomeEligible,
        matchingCriteria: isIncomeEligible
          ? ['BPL Ration Card Holder', 'Income below statutory ceiling', 'Empaneled Specialty Match']
          : ['General Ration Category'],
        potentialSupportAmount: isIncomeEligible ? Math.min(s.maxBenefitAmount, 150000) : 0,
        applicationStatus: isIncomeEligible ? 'APPLIED' : 'NOT_APPLIED'
      };
    });
  },

  calculateCareToCost: (
    estimatedCost: number,
    insuranceAmount: number,
    govSchemeAmount: number,
    ngoAmount: number,
    selfPayAmount: number
  ): CareToCostAssessment => {
    const totalAid = insuranceAmount + govSchemeAmount + ngoAmount + selfPayAmount;
    const gap = Math.max(0, estimatedCost - totalAid);

    const assessment: CareToCostAssessment = {
      id: `ctc-${Date.now()}`,
      patientId: db.getPatientProfile().userId,
      hospitalName: 'CarePlus Super Specialty Hospital',
      estimatedTreatmentCost: estimatedCost,
      insuranceCoverage: insuranceAmount,
      governmentSupport: govSchemeAmount,
      ngoAssistance: ngoAmount,
      patientSelfContribution: selfPayAmount,
      financialGap: gap,
      isFundingComplete: gap === 0,
      calculatedAt: new Date().toLocaleString('en-IN')
    };

    db.saveCareToCostAssessment(assessment);
    return assessment;
  },

  getFinanceScenarios: (baseCost: number): FinanceScenario[] => {
    return [
      {
        id: 'scen-a',
        scenarioTitle: 'Scenario A: Selected Hospital (CarePlus Tertiary)',
        hospitalName: 'CarePlus Super Specialty',
        estimatedCost: baseCost,
        insuranceBenefit: 60000,
        governmentBenefit: 30000,
        ngoBenefit: 15000,
        patientOutofPocket: 15000,
        remainingGap: 0,
        recommendationTag: 'CURRENT SELECTION'
      },
      {
        id: 'scen-b',
        scenarioTitle: 'Scenario B: AIIMS Public Referral (Full Subsidy)',
        hospitalName: 'AIIMS Regional Emergency Center',
        estimatedCost: 35000,
        insuranceBenefit: 0,
        governmentBenefit: 35000,
        ngoBenefit: 0,
        patientOutofPocket: 0,
        remainingGap: 0,
        recommendationTag: 'LOWEST OUT-OF-POCKET'
      },
      {
        id: 'scen-c',
        scenarioTitle: 'Scenario C: Community Hospital (Empaneled MJPJAY)',
        hospitalName: 'City Community Health Center',
        estimatedCost: 55000,
        insuranceBenefit: 30000,
        governmentBenefit: 25000,
        ngoBenefit: 0,
        patientOutofPocket: 0,
        remainingGap: 0,
        recommendationTag: 'ZERO GAP ALTERNATIVE'
      }
    ];
  }
};
