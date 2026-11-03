import React, { useState, useEffect } from 'react';
import { db } from '../../db/database';
import type { TreatmentCostEstimate, OPDRegistration, MedicalRecord, TriageResult, DoctorScheduleItem, BlockedSlotInfo, PatientProfile } from '../../types';
import { TreatmentCostGenerator } from './TreatmentCostGenerator';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import {
  Stethoscope,
  User,
  FileText,
  Lock,
  CheckCircle2,
  Calendar,
  Clock,
  Award,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  ChevronRight,
  Calculator,
  Plus,
  Trash2,
  Edit3,
  RotateCcw,
  Loader2,
  Download,
  AlertTriangle
} from 'lucide-react';
import { Button, Card, Badge, EmptyState } from '../common/UIComponents';
import { opdService, recordService, consentService, consultationService, triageService, doctorService, patientService } from '../../services/apiServices';

interface Props {
  onCostEstimateCreated: (est: TreatmentCostEstimate) => void;
}

export const DoctorDashboard: React.FC<Props> = ({ onCostEstimateCreated }) => {
  const currentUser = db.getCurrentUser();
  const currentDoctorId = currentUser?.doctorProfile?.id || (currentUser?.id === 'usr-doctor-1' ? 'doc-1' : currentUser?.id || 'doc-1');
  const currentDoctorName = currentUser?.name || 'Dr. Rajesh Kulkarni';
  const currentHospitalId = currentUser?.hospitalId || 'hosp-1';

  // Selected Patient Clinical Context (strictly scoped to the selected appointment, never defaulting to demo localStorage)
  const [selectedPatientProfile, setSelectedPatientProfile] = useState<PatientProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState<boolean>(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [patientTriage, setPatientTriage] = useState<TriageResult | null>(null);

  const [opds, setOpds] = useState<OPDRegistration[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState<boolean>(true);
  const [queueError, setQueueError] = useState<string | null>(null);

  const [patientRecords, setPatientRecords] = useState<MedicalRecord[]>([]);
  const [isConsentActive, setIsConsentActive] = useState<boolean>(false);
  const [isLoadingRecords, setIsLoadingRecords] = useState<boolean>(false);
  const [isRequestingConsent, setIsRequestingConsent] = useState<boolean>(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownloadRecord = async (recordId: string, fileName?: string) => {
    setDownloadingId(recordId);
    try {
      await recordService.downloadRecordFile(recordId, fileName);
    } catch (err: any) {
      alert(`Download failed: ${err?.message || 'Active patient consent is required to download records.'}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const [activeTab, setActiveTab] = useState<'QUEUE' | 'CONSULTATION' | 'SCHEDULE' | 'PROFILE'>('QUEUE');

  // Consultation State
  const [selectedAppointment, setSelectedAppointment] = useState<OPDRegistration | null>(null);

  const checkConsentAndLoadRecords = async () => {
    if (!selectedAppointment?.patientId) {
      setSelectedPatientProfile(null);
      setPatientRecords([]);
      setPatientTriage(null);
      setIsConsentActive(false);
      return;
    }
    setIsLoadingRecords(true);
    try {
      const recs = await recordService.getRecords(selectedAppointment.patientId);
      setPatientRecords(recs);
      setIsConsentActive(true);
    } catch {
      setIsConsentActive(false);
      setPatientRecords([]);
    } finally {
      setIsLoadingRecords(false);
    }

    setIsLoadingProfile(true);
    setProfileError(null);
    try {
      const prof = await patientService.getProfile(selectedAppointment.patientId);
      setSelectedPatientProfile(prof);
    } catch (err: any) {
      setSelectedPatientProfile(null);
      setProfileError(err?.message || 'Access to patient clinical profile denied or unavailable.');
    } finally {
      setIsLoadingProfile(false);
    }

    try {
      const triages = await triageService.getTriageResults(selectedAppointment.patientId);
      if (triages && triages.length > 0) {
        setPatientTriage(triages[0]);
      } else {
        setPatientTriage(null);
      }
    } catch {
      setPatientTriage(null);
    }
  };

  useEffect(() => {
    if (activeTab === 'CONSULTATION' && selectedAppointment) {
      checkConsentAndLoadRecords();
    } else {
      setSelectedPatientProfile(null);
      setProfileError(null);
      setIsConsentActive(false);
      setPatientRecords([]);
    }
  }, [activeTab, selectedAppointment?.id, selectedAppointment?.patientId]);

  const handleDoctorRequestConsent = async () => {
    if (!selectedAppointment) return;
    setIsRequestingConsent(true);
    try {
      await consentService.grantConsent({
        patientId: selectedAppointment.patientId,
        hospitalId: selectedAppointment.hospitalId || currentHospitalId,
        hospitalName: selectedAppointment.hospitalName || 'CarePlus Super Specialty Hospital',
        doctorId: currentDoctorId,
        doctorName: currentDoctorName,
        granted: false
      });
      alert(`Access consent requested! Patient ${selectedAppointment.patientName} can approve it from their Patient Dashboard.`);
    } catch (err: any) {
      alert(err?.message || 'Failed to dispatch consent request.');
    } finally {
      setIsRequestingConsent(false);
    }
  };

  const fetchDoctorAppointments = async () => {
    setIsLoadingQueue(true);
    setQueueError(null);
    try {
      const data = await opdService.getAppointments({ doctorId: currentDoctorId });
      setOpds(data);
      if (data.length > 0) {
        setSelectedAppointment(prev => {
          if (!prev) return data[0];
          const found = data.find(d => d.id === prev.id);
          return found || data[0];
        });
      }
    } catch (err: any) {
      console.error('Failed to load doctor appointments:', err);
      setQueueError(err?.message || 'Failed to load appointments from server.');
      setOpds(db.getOPDRegistrations());
    } finally {
      setIsLoadingQueue(false);
    }
  };

  useEffect(() => {
    fetchDoctorAppointments();
    fetchDoctorSchedule();
  }, []);

  const [clinicalNotes, setClinicalNotes] = useState(
    'Patient presented with mild effort-induced chest tightness. Vitals stable. EKG shows normal sinus rhythm without acute ischemic changes.'
  );
  const [diagnosis, setDiagnosis] = useState(
    'Suspected Angina Pectoris / Ischemic Heart Disease Evaluation Required'
  );
  const [treatmentPlan, setTreatmentPlan] = useState(
    'Advised 2D Echocardiogram, Trop-I, and Coronary Angiography evaluation.'
  );

  const [prescriptions, setPrescriptions] = useState<{ name: string; dosage: string; duration: string }[]>([
    { name: 'Sorbitrate 5mg', dosage: 'Sublingual PRN', duration: '5 days' },
    { name: 'Aspirin 75mg', dosage: '1-0-0 (Post Meal)', duration: '30 days' },
    { name: 'Atorvastatin 20mg', dosage: '0-0-1 (Bedtime)', duration: '30 days' }
  ]);

  const [newMedName, setNewMedName] = useState('');
  const [newMedDosage, setNewMedDosage] = useState('1-0-1');
  const [newMedDuration, setNewMedDuration] = useState('7 days');

  const [isCostModalOpen, setIsCostModalOpen] = useState(false);
  const [isFinalized, setIsFinalized] = useState(false);
  const [isSubmittingConsultation, setIsSubmittingConsultation] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [consultationError, setConsultationError] = useState<string | null>(null);
  const [consultationSuccess, setConsultationSuccess] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadExistingConsultation = async () => {
      if (!selectedAppointment?.id) return;
      if (selectedAppointment.status === 'COMPLETED') {
        setIsFinalized(true);
        try {
          const existing = await consultationService.getConsultation(selectedAppointment.id);
          if (existing && isMounted) {
            if (existing.clinicalNotes) setClinicalNotes(existing.clinicalNotes);
            if (existing.diagnosis) setDiagnosis(existing.diagnosis);
            if (existing.treatmentPlan) setTreatmentPlan(existing.treatmentPlan);
            if (Array.isArray(existing.prescriptionMedicines) && existing.prescriptionMedicines.length > 0) {
              setPrescriptions(existing.prescriptionMedicines);
            }
          }
        } catch (err) {
          console.warn('Could not load consultation record:', err);
        }
      } else {
        setIsFinalized(false);
        setConsultationError(null);
        setConsultationSuccess(null);
        // Check for existing saved draft on server
        try {
          const draft = await consultationService.getDraft(selectedAppointment.id);
          if (draft && isMounted) {
            if (draft.clinicalNotes) setClinicalNotes(draft.clinicalNotes);
            if (draft.diagnosis) setDiagnosis(draft.diagnosis);
            if (draft.treatmentPlan) setTreatmentPlan(draft.treatmentPlan);
            if (Array.isArray(draft.prescriptionMedicines) && draft.prescriptionMedicines.length > 0) {
              setPrescriptions(draft.prescriptionMedicines);
            }
            setConsultationSuccess('Loaded saved consultation draft from server.');
          }
        } catch (err) {
          // ignore draft load errors
        }
      }
    };

    if (activeTab === 'CONSULTATION') {
      loadExistingConsultation();
    }
    return () => { isMounted = false; };
  }, [activeTab, selectedAppointment?.id, selectedAppointment?.status]);

  // Schedule Slots State
  const [doctorSchedule, setDoctorSchedule] = useState<DoctorScheduleItem[]>([]);
  const [blockedSlots, setBlockedSlots] = useState<(BlockedSlotInfo | string)[]>([]);
  const [isLoadingSchedule, setIsLoadingSchedule] = useState<boolean>(true);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleSuccess, setScheduleSuccess] = useState<string | null>(null);
  const [isUpdatingSlot, setIsUpdatingSlot] = useState<number | null>(null);

  const fetchDoctorSchedule = async () => {
    setIsLoadingSchedule(true);
    setScheduleError(null);
    try {
      const data = await doctorService.getDoctorSchedule();
      setDoctorSchedule(data.weeklySchedule || []);
      setBlockedSlots(data.blockedSlots || []);
    } catch (err: any) {
      console.warn('Failed to load doctor schedule:', err);
      setScheduleError(err?.message || 'Failed to load clinic schedule from server.');
    } finally {
      setIsLoadingSchedule(false);
    }
  };

  const handleAddMedicine = () => {
    if (!newMedName.trim()) return;
    setPrescriptions(prev => [
      ...prev,
      { name: newMedName.trim(), dosage: newMedDosage, duration: newMedDuration }
    ]);
    setNewMedName('');
  };

  const handleRemoveMedicine = (idx: number) => {
    setPrescriptions(prev => prev.filter((_, i) => i !== idx));
  };

  const handleSaveDraft = async () => {
    if (!selectedAppointment?.id) {
      setConsultationError('No active appointment selected.');
      return;
    }
    setIsSavingDraft(true);
    setConsultationError(null);
    setConsultationSuccess(null);
    try {
      await consultationService.saveDraft({
        appointmentId: selectedAppointment.id,
        clinicalNotes: clinicalNotes.trim(),
        diagnosis: diagnosis.trim(),
        treatmentPlan: treatmentPlan.trim(),
        prescriptionMedicines: prescriptions,
        investigationsOrdered: ['2D Echocardiogram', 'Troponin-I Level', 'Coronary Angiography']
      });
      setConsultationSuccess('Consultation draft saved to secure server! You can resume editing anytime.');
    } catch (err: any) {
      setConsultationError(err?.message || 'Failed to save consultation draft to server.');
    } finally {
      setIsSavingDraft(false);
    }
  };

  const handleFinalizeConsultation = async () => {
    if (!selectedAppointment?.id) {
      setConsultationError('No active appointment selected to finalize.');
      return;
    }

    if (!diagnosis.trim()) {
      setConsultationError('Diagnosis is required.');
      return;
    }
    if (!clinicalNotes.trim()) {
      setConsultationError('Clinical notes are required.');
      return;
    }
    if (!treatmentPlan.trim()) {
      setConsultationError('Treatment plan is required.');
      return;
    }

    setIsSubmittingConsultation(true);
    setConsultationError(null);
    setConsultationSuccess(null);

    try {
      await consultationService.finalizeConsultation({
        appointmentId: selectedAppointment.id,
        patientId: selectedAppointment.patientId,
        clinicalNotes: clinicalNotes.trim(),
        diagnosis: diagnosis.trim(),
        investigationsOrdered: ['2D Echocardiogram', 'Troponin-I Level', 'Coronary Angiography'],
        prescriptionMedicines: prescriptions,
        treatmentPlan: treatmentPlan.trim()
      });

      setIsFinalized(true);
      setConsultationSuccess('Consultation finalized and signed! Prescriptions and notes dispatched to patient health profile.');
      await fetchDoctorAppointments();
    } catch (err: any) {
      console.error('Failed to finalize consultation:', err);
      setConsultationError(err?.message || 'Failed to finalize consultation. Please try again.');
    } finally {
      setIsSubmittingConsultation(false);
    }
  };

  const handleToggleBlockSlot = async (index: number) => {
    const item = doctorSchedule[index];
    if (!item) return;

    setIsUpdatingSlot(index);
    setScheduleError(null);
    setScheduleSuccess(null);

    try {
      if (item.isBlocked) {
        const res = await doctorService.unblockSlot({ day: item.day });
        setDoctorSchedule(res.weeklySchedule);
        setBlockedSlots(res.blockedSlots);
        setScheduleSuccess(`Slot for ${item.day} unblocked successfully! Availability restored.`);
      } else {
        const res = await doctorService.blockSlot({ day: item.day });
        setDoctorSchedule(res.weeklySchedule);
        setBlockedSlots(res.blockedSlots);
        setScheduleSuccess(`Slot for ${item.day} blocked successfully! Saved to SQLite database.`);
      }
    } catch (err: any) {
      setScheduleError(err?.message || `Failed to update slot for ${item.day}.`);
    } finally {
      setIsUpdatingSlot(null);
    }
  };

  const handleUnblockSpecificSlot = async (slotIdentifier: string) => {
    setScheduleError(null);
    setScheduleSuccess(null);
    try {
      const res = await doctorService.unblockSlot({ slot: slotIdentifier });
      setDoctorSchedule(res.weeklySchedule);
      setBlockedSlots(res.blockedSlots);
      setScheduleSuccess(`Slot ${slotIdentifier} unblocked successfully!`);
    } catch (err: any) {
      setScheduleError(err?.message || `Failed to unblock slot.`);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Doctor Header Banner */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-light)',
          borderRadius: '20px',
          padding: '24px 28px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '14px',
              background: 'rgba(124, 58, 237, 0.12)',
              color: '#7C3AED',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Stethoscope size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
              <Badge variant="purple">DOCTOR WORKSPACE</Badge>
              <span className="badge badge-teal" style={{ fontSize: '0.72rem' }}>
                <ShieldCheck size={12} /> NMC VERIFIED: MCI-2014-998124
              </span>
            </div>
            <h1 style={{ fontSize: '1.6rem', color: 'var(--text-heading)', margin: 0 }}>
              Dr. Rajesh Kulkarni, MD, DM
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '2px 0 0' }}>
              Senior Interventional Cardiologist • CarePlus Super Specialty Hospital (Cardiology OPD)
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Button
            variant="teal"
            size="sm"
            onClick={() => setIsCostModalOpen(true)}
            leftIcon={<Calculator size={15} />}
          >
            Generate Cost Estimate
          </Button>
        </div>
      </div>

      <DisclaimerBanner text="Doctor Decision-Support Workspace. Clinical observations and treatments must conform to professional standards of medical practice." />

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-light)',
          marginBottom: '24px',
          paddingBottom: '8px',
          overflowX: 'auto'
        }}
      >
        <button
          onClick={() => setActiveTab('QUEUE')}
          className={`btn btn-sm ${activeTab === 'QUEUE' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Calendar size={15} /> Today's Patient Queue ({opds.length})
        </button>
        <button
          onClick={() => setActiveTab('CONSULTATION')}
          className={`btn btn-sm ${activeTab === 'CONSULTATION' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <FileText size={15} /> Consultation Workspace
        </button>
        <button
          onClick={() => setActiveTab('SCHEDULE')}
          className={`btn btn-sm ${activeTab === 'SCHEDULE' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Clock size={15} /> My OPD Schedule &amp; Slots
        </button>
        <button
          onClick={() => setActiveTab('PROFILE')}
          className={`btn btn-sm ${activeTab === 'PROFILE' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Award size={15} /> Doctor Credentials
        </button>
      </div>

      {/* TAB 1: TODAY'S PATIENT QUEUE */}
      {activeTab === 'QUEUE' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0 }}>
                OPD Patient Queue for Today
              </h2>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Cardiology Consultation Room 204 • Synchronized with Central Hospital Database
              </span>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={fetchDoctorAppointments}
              isLoading={isLoadingQueue}
              leftIcon={<RotateCcw size={14} />}
            >
              Refresh Queue
            </Button>
          </div>

          {queueError && (
            <div style={{
              padding: '12px 16px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--accent-red)',
              borderRadius: '8px',
              color: 'var(--accent-red)',
              marginBottom: '14px',
              fontSize: '0.85rem'
            }}>
              {queueError}
            </div>
          )}

          {isLoadingQueue ? (
            <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-muted)' }}>
              <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto 12px', display: 'block', color: 'var(--primary-teal)' }} />
              <p style={{ margin: 0, fontSize: '0.9rem' }}>Fetching real-time patient queue from backend...</p>
            </div>
          ) : opds.length === 0 ? (
            <EmptyState
              icon={<Calendar size={32} />}
              title="No Patients Scheduled in Queue"
              description="There are currently no confirmed or checked-in patients in your OPD queue for today."
              actionLabel="Check Backend Schedule"
              onAction={fetchDoctorAppointments}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {opds.map((opd, idx) => (
                <Card
                  key={opd.id}
                  padding="18px 22px"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background: 'var(--bg-subtle)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 800,
                        color: 'var(--primary-teal)',
                        fontSize: '1.1rem'
                      }}
                    >
                      #{idx + 1}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                        <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--text-heading)' }}>
                          {opd.patientName}
                        </h4>
                        <Badge variant={opd.status === 'VERIFIED' ? 'green' : opd.status === 'CANCELLED' ? 'red' : 'teal'} size="sm">
                          {opd.status === 'VERIFIED' ? 'Checked-In via QR' : opd.status}
                        </Badge>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          REF: {opd.referenceId}
                        </span>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        Contact: {opd.patientPhone} • Slot: <strong>{opd.appointmentDate} at {opd.appointmentTime}</strong>
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    {opd.status !== 'CANCELLED' && (
                      <Button
                        variant="teal"
                        size="sm"
                        onClick={() => {
                          setSelectedAppointment(opd);
                          setActiveTab('CONSULTATION');
                        }}
                        rightIcon={<ChevronRight size={14} />}
                      >
                        Start Consultation
                      </Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CONSULTATION WORKSPACE */}
      {activeTab === 'CONSULTATION' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>
          {/* Left Column: Authorized Patient Medical File (Consent Guarded) */}
          <div>
            <Card padding="24px" style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <User size={18} color="var(--primary-teal)" />
                  Authorized Patient Clinical Summary
                </h3>
                <Badge variant={isConsentActive ? 'green' : 'amber'} size="sm">
                  {isConsentActive ? '✓ Consent Active' : '🔒 Consent Required'}
                </Badge>
              </div>

              {!isConsentActive ? (
                <div
                  style={{
                    background: 'rgba(217, 119, 6, 0.08)',
                    border: '1px solid #D97706',
                    borderRadius: '12px',
                    padding: '20px',
                    textAlign: 'center'
                  }}
                >
                  <Lock size={32} color="#D97706" style={{ margin: '0 auto 8px' }} />
                  <h4 style={{ margin: '0 0 6px', color: 'var(--text-heading)' }}>Medical Access Guard</h4>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                    ABDM privacy protocol requires the patient to grant digital consent before clinical records are unlocked.
                  </p>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                    <Button
                      variant="teal"
                      size="sm"
                      onClick={handleDoctorRequestConsent}
                      disabled={isRequestingConsent || !selectedAppointment}
                    >
                      {isRequestingConsent ? 'Requesting...' : 'Request Patient Consent'}
                    </Button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* Demographics */}
                  <div style={{ background: 'var(--bg-subtle)', padding: '12px', borderRadius: '10px', fontSize: '0.85rem' }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-heading)', fontSize: '1rem' }}>
                      {selectedAppointment?.patientName || selectedPatientProfile?.fullName || 'Selected Patient'}
                    </div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>
                      Ref: {selectedAppointment?.referenceId || 'N/A'} • Dept: {selectedAppointment?.department || 'Cardiology'} • Fee: ₹{selectedAppointment?.consultationFee || 0}
                    </div>
                  </div>

                  {/* Vitals */}
                  <div>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                      Recorded Vital Signs
                    </span>
                    {isLoadingProfile ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '12px 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        <Loader2 size={14} className="spin" /> Loading clinical vitals...
                      </div>
                    ) : selectedPatientProfile?.vitalSigns ? (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', textAlign: 'center', marginTop: '4px' }}>
                        <div style={{ background: 'var(--bg-subtle)', padding: '8px 4px', borderRadius: '8px', fontSize: '0.8rem' }}>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>BP</div>
                          <strong>{selectedPatientProfile.vitalSigns.bp || 'N/A'}</strong>
                        </div>
                        <div style={{ background: 'var(--bg-subtle)', padding: '8px 4px', borderRadius: '8px', fontSize: '0.8rem' }}>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>PULSE</div>
                          <strong>{selectedPatientProfile.vitalSigns.pulse || 'N/A'}</strong>
                        </div>
                        <div style={{ background: 'var(--bg-subtle)', padding: '8px 4px', borderRadius: '8px', fontSize: '0.8rem' }}>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>SPO2</div>
                          <strong style={{ color: '#16A34A' }}>{selectedPatientProfile.vitalSigns.spo2 || 'N/A'}</strong>
                        </div>
                        <div style={{ background: 'var(--bg-subtle)', padding: '8px 4px', borderRadius: '8px', fontSize: '0.8rem' }}>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>TEMP</div>
                          <strong>{selectedPatientProfile.vitalSigns.temp || 'N/A'}</strong>
                        </div>
                      </div>
                    ) : (
                      <div style={{ background: 'var(--bg-subtle)', padding: '10px', borderRadius: '8px', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {profileError ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#B91C1C' }}>
                            <ShieldAlert size={14} /> {profileError}
                          </div>
                        ) : (
                          'No vitals recorded for this patient profile.'
                        )}
                      </div>
                    )}
                  </div>

                  {/* Medical Records Unlocked */}
                  <div>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                      Unlocked Digital Records ({patientRecords.length})
                    </span>
                    {isLoadingRecords ? (
                      <div style={{ textAlign: 'center', padding: '12px' }}>
                        <Loader2 size={16} className="spin" />
                      </div>
                    ) : patientRecords.length === 0 ? (
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', padding: '8px 0' }}>
                        No records uploaded yet for this patient.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                        {patientRecords.map(rec => (
                          <div
                            key={rec.id}
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              padding: '8px 10px',
                              background: 'var(--bg-subtle)',
                              borderRadius: '8px',
                              border: '1px solid var(--border-light)',
                              fontSize: '0.82rem'
                            }}
                          >
                            <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-heading)' }}>{rec.fileName}</div>
                              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{rec.category} • {rec.uploadDate}</div>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDownloadRecord(rec.id, rec.fileName)}
                              disabled={downloadingId === rec.id}
                              leftIcon={<Download size={13} />}
                              style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            >
                              {downloadingId === rec.id ? 'Downloading...' : 'Download'}
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* AI Triage Synthesis */}
                  {patientTriage && (
                    <div style={{ background: 'var(--bg-subtle)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                        <Sparkles size={14} color="var(--primary-teal)" />
                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary-teal)' }}>AI TRIAGE SUMMARY</span>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-heading)', fontWeight: 600 }}>
                        Risk: {patientTriage.riskLevel} • {patientTriage.urgency}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Symptoms: {patientTriage.symptomsConsidered.join(', ')}
                      </div>
                    </div>
                  )}

                  {/* Active Meds & Allergies */}
                  <div>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                      Current Medications &amp; Allergies
                    </span>
                    {isLoadingProfile ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        <Loader2 size={14} className="spin" /> Loading medications &amp; allergies...
                      </div>
                    ) : selectedPatientProfile ? (
                      <>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '4px' }}>
                          Rx: <strong>{selectedPatientProfile.medications && selectedPatientProfile.medications.length > 0 ? selectedPatientProfile.medications.join(', ') : 'None documented'}</strong>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#DC2626', marginTop: '2px' }}>
                          Allergy: <strong>{selectedPatientProfile.allergies && selectedPatientProfile.allergies.length > 0 ? selectedPatientProfile.allergies.join(', ') : 'No known drug allergies (NKDA)'}</strong>
                        </div>
                      </>
                    ) : (
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Medical history not loaded.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </Card>

            {/* Quick Button to Launch Cost Estimate Generator */}
            <Card padding="20px" style={{ background: 'rgba(2, 132, 199, 0.06)', border: '1px solid rgba(2, 132, 199, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <Calculator size={20} color="var(--primary-teal)" />
                <h4 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-heading)' }}>
                  Treatment Cost Generator
                </h4>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                Generate an itemized treatment estimate (procedure, ICU/room, labs, medicines) to instantly unlock patient financial gap subsidies under PM-JAY.
              </p>
              <Button
                variant="teal"
                size="sm"
                onClick={() => setIsCostModalOpen(true)}
                leftIcon={<Calculator size={14} />}
                style={{ width: '100%' }}
              >
                Open Cost Estimate Form
              </Button>
            </Card>
          </div>

          {/* Right Column: Doctor Consultation Pad & Prescription Pad */}
          <div>
            <Card padding="28px">
              <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Edit3 size={18} color="var(--primary-teal)" />
                Doctor Consultation &amp; Prescription Pad
              </h3>

              {/* Diagnosis */}
              <div style={{ marginBottom: '16px' }}>
                <label className="form-label">Clinical Diagnosis / Impression</label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={e => setDiagnosis(e.target.value)}
                  className="form-control"
                />
              </div>

              {/* Clinical Notes */}
              <div style={{ marginBottom: '16px' }}>
                <label className="form-label">Consultation Notes &amp; Examination</label>
                <textarea
                  rows={3}
                  value={clinicalNotes}
                  onChange={e => setClinicalNotes(e.target.value)}
                  className="form-control"
                  style={{ resize: 'vertical' }}
                />
              </div>

              {/* Prescriptions */}
              <div style={{ marginBottom: '16px' }}>
                <label className="form-label">Prescription Medicines</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
                  {prescriptions.map((p, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        background: 'var(--bg-subtle)',
                        borderRadius: '8px',
                        border: '1px solid var(--border-light)',
                        fontSize: '0.86rem'
                      }}
                    >
                      <div>
                        <strong>{p.name}</strong> • {p.dosage} • {p.duration}
                      </div>
                      <button
                        onClick={() => handleRemoveMedicine(idx)}
                        style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    value={newMedName}
                    onChange={e => setNewMedName(e.target.value)}
                    placeholder="Medicine Name (e.g. Clopidogrel 75mg)..."
                    className="form-control"
                    style={{ flex: 2, minWidth: '160px', height: '36px', fontSize: '0.84rem' }}
                  />
                  <input
                    type="text"
                    value={newMedDosage}
                    onChange={e => setNewMedDosage(e.target.value)}
                    placeholder="1-0-1"
                    className="form-control"
                    style={{ flex: 1, minWidth: '80px', height: '36px', fontSize: '0.84rem' }}
                  />
                  <input
                    type="text"
                    value={newMedDuration}
                    onChange={e => setNewMedDuration(e.target.value)}
                    placeholder="15 days"
                    className="form-control"
                    style={{ flex: 1, minWidth: '80px', height: '36px', fontSize: '0.84rem' }}
                  />
                  <Button variant="secondary" size="sm" onClick={handleAddMedicine} leftIcon={<Plus size={14} />}>
                    Add
                  </Button>
                </div>
              </div>

              {/* Treatment Plan & Follow-up */}
              <div style={{ marginBottom: '20px' }}>
                <label className="form-label">Treatment Plan &amp; Follow-up Advice</label>
                <textarea
                  rows={2}
                  value={treatmentPlan}
                  onChange={e => setTreatmentPlan(e.target.value)}
                  className="form-control"
                />
              </div>

              {/* Consultation Error & Success Messages */}
              {consultationError && (
                <div style={{ marginBottom: '14px', padding: '10px 14px', borderRadius: '8px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', fontSize: '0.85rem' }}>
                  {consultationError}
                </div>
              )}
              {consultationSuccess && (
                <div style={{ marginBottom: '14px', padding: '10px 14px', borderRadius: '8px', background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', fontSize: '0.85rem' }}>
                  {consultationSuccess}
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <Button variant="secondary" onClick={handleSaveDraft} disabled={isFinalized || isSubmittingConsultation || isSavingDraft}>
                  {isSavingDraft ? 'Saving Draft...' : 'Save Draft'}
                </Button>
                <Button
                  variant="teal"
                  onClick={handleFinalizeConsultation}
                  disabled={isFinalized || isSubmittingConsultation}
                  leftIcon={isSubmittingConsultation ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                >
                  {isSubmittingConsultation ? 'Finalizing...' : isFinalized ? 'Consultation Finalized ✓' : 'Finalize & Sign Rx'}
                </Button>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 3: SCHEDULE & SLOTS */}
      {activeTab === 'SCHEDULE' && (
        <Card padding="28px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
                Weekly OPD Availability &amp; Timetable
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>
                Toggle active days and block emergency leave slots. Available slots are instantly synchronized across Patient and Hospital panels.
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchDoctorSchedule}
              disabled={isLoadingSchedule}
              leftIcon={<RotateCcw size={14} className={isLoadingSchedule ? 'animate-spin' : ''} />}
            >
              Refresh
            </Button>
          </div>

          {/* Feedback Banners */}
          {scheduleError && (
            <div style={{ margin: '16px 0', padding: '12px 16px', borderRadius: '10px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} color="#DC2626" />
              <span>{scheduleError}</span>
            </div>
          )}
          {scheduleSuccess && (
            <div style={{ margin: '16px 0', padding: '12px 16px', borderRadius: '10px', background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} color="#16A34A" />
              <span>{scheduleSuccess}</span>
            </div>
          )}

          {isLoadingSchedule ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto 12px', color: 'var(--primary-teal)' }} />
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading persisted doctor schedule from SQLite...</p>
            </div>
          ) : doctorSchedule.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
              No weekly schedule configured. Click refresh to initialize standard timetable.
            </div>
          ) : (
            <table className="health-table" style={{ marginTop: '14px' }}>
              <thead>
                <tr>
                  <th>Day</th>
                  <th>OPD Hours</th>
                  <th>Slot Quota</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {doctorSchedule.map((item, idx) => (
                  <tr key={item.day}>
                    <td><strong>{item.day}</strong></td>
                    <td>{item.time}</td>
                    <td>{item.slots} Appointments</td>
                    <td>
                      <Badge variant={item.isBlocked ? 'red' : 'green'} size="sm">
                        {item.isBlocked ? 'Blocked / Unavailable' : 'Active Open'}
                      </Badge>
                    </td>
                    <td>
                      <Button
                        variant={item.isBlocked ? 'teal' : 'secondary'}
                        size="sm"
                        disabled={isUpdatingSlot === idx}
                        onClick={() => handleToggleBlockSlot(idx)}
                        leftIcon={isUpdatingSlot === idx ? <Loader2 size={14} className="animate-spin" /> : undefined}
                      >
                        {isUpdatingSlot === idx
                          ? (item.isBlocked ? 'Unblocking...' : 'Blocking...')
                          : (item.isBlocked ? 'Unblock Slot' : 'Block Slot')}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Blocked Specific Slots Section */}
          {blockedSlots && blockedSlots.length > 0 && (
            <div style={{ marginTop: '30px', borderTop: '1px solid var(--border-light)', paddingTop: '20px' }}>
              <h3 style={{ fontSize: '1.05rem', color: 'var(--text-heading)', margin: '0 0 10px' }}>
                Specifically Blocked Date/Time Slots ({blockedSlots.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {blockedSlots.map((b, bIdx) => {
                  const slotKey = typeof b === 'string' ? b : (b.slot || `${b.date}#${b.time}`);
                  const label = typeof b === 'string' ? b : `${b.date || b.day} at ${b.time || ''} — ${b.reason || 'Blocked'}`;
                  return (
                    <div
                      key={bIdx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '10px 14px',
                        background: 'var(--bg-subtle)',
                        borderRadius: '10px',
                        border: '1px solid var(--border-light)',
                        fontSize: '0.85rem'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Badge variant="red" size="sm">BLOCKED</Badge>
                        <span style={{ fontWeight: 600 }}>{label}</span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUnblockSpecificSlot(slotKey)}
                      >
                        Unblock Slot
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* TAB 4: DOCTOR PROFILE & NMC REGISTRATION */}
      {activeTab === 'PROFILE' && (
        <Card padding="28px">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <img
              src="https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=200&q=80"
              alt="Dr. Rajesh Kulkarni"
              style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover' }}
            />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.4rem', color: 'var(--text-heading)', margin: 0 }}>Dr. Rajesh Kulkarni</h2>
                <Badge variant="teal" size="sm">NMC VERIFIED</Badge>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '2px 0 0' }}>
                MBBS, MD (General Medicine), DM (Cardiology), FACC
              </p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', margin: '2px 0 0' }}>
                National Medical Commission Registration: <strong>MCI-2014-998124</strong>
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', fontSize: '0.9rem' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>PRIMARY SPECIALIZATION</span>
              <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>Interventional Cardiology</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>CLINICAL EXPERIENCE</span>
              <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>16+ Years Tertiary Care</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>HOSPITAL AFFILIATION</span>
              <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>CarePlus Super Specialty (Pune)</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>STANDARD OPD FEE</span>
              <div style={{ fontWeight: 700, color: '#16A34A', marginTop: '2px' }}>₹800 / Visit</div>
            </div>
          </div>
        </Card>
      )}

      {/* Itemized Treatment Cost Estimate Generator Modal */}
      <TreatmentCostGenerator
        isOpen={isCostModalOpen}
        hospitalId={selectedAppointment?.hospitalId || currentHospitalId}
        hospitalName={selectedAppointment?.hospitalName || 'CarePlus Super Specialty Hospital'}
        patientId={selectedAppointment?.patientId || ''}
        patientName={selectedAppointment?.patientName || selectedPatientProfile?.fullName || 'Patient'}
        consultationId={selectedAppointment?.id}
        onClose={() => setIsCostModalOpen(false)}
        onEstimateGenerated={(est: TreatmentCostEstimate) => {
          setIsCostModalOpen(false);
          onCostEstimateCreated(est);
        }}
      />
    </div>
  );
};
