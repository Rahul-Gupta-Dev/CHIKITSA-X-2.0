import React, { useState, useEffect } from 'react';
import { db } from '../../db/database';
import { patientService, consentService } from '../../services/apiServices';
import type { PatientProfile, PatientConsent } from '../../types';
import { CareJourneyTimeline } from '../common/CareJourneyTimeline';
import { HospitalPassQR } from './HospitalPassQR';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import {
  Mic,
  FileText,
  Activity,
  Building2,
  Calendar,
  QrCode,
  Wallet,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Lock,
  Heart,
  Stethoscope
} from 'lucide-react';
import { Button, Card, Badge } from '../common/UIComponents';

interface Props {
  onOpenVoiceIntake: () => void;
  onOpenOCR: () => void;
  onOpenHealthProfile: () => void;
  onOpenTriage: () => void;
  onOpenHospitals: () => void;
  onOpenBookAppointment: () => void;
  onOpenMyAppointments: () => void;
  onOpenFinancialSupport: () => void;
  onOpenFinancePlanner: () => void;
  onOpenEmergency: () => void;
}

export const PatientDashboard: React.FC<Props> = ({
  onOpenVoiceIntake,
  onOpenOCR,
  onOpenHealthProfile,
  onOpenTriage,
  onOpenHospitals,
  onOpenBookAppointment,
  onOpenMyAppointments,
  onOpenFinancialSupport,
  onOpenFinancePlanner,
  onOpenEmergency
}) => {
  const [profile, setProfile] = useState<PatientProfile>(() => db.getPatientProfile());
  const opdList = db.getOPDRegistrations();
  const activeOPD = opdList.find(o => o.status === 'CONFIRMED' || o.status === 'VERIFIED') || null;
  const [consents, setConsents] = useState<PatientConsent[]>([]);
  const [isGranting, setIsGranting] = useState(false);
  const pendingConsent = consents.find(c => c.status === 'PENDING');

  const [showQRModal, setShowQRModal] = useState(false);

  useEffect(() => {
    const user = db.getCurrentUser();
    const uid = user?.id || 'me';
    patientService.getProfile(uid).then(p => { if (p) setProfile(p); }).catch(() => {});
    consentService.getConsents(uid).then(c => { if (Array.isArray(c)) setConsents(c); }).catch(() => {});
  }, []);

  const handleGrantConsent = async (consent: PatientConsent) => {
    setIsGranting(true);
    try {
      await consentService.grantConsent({
        patientId: consent.patientId,
        hospitalId: consent.hospitalId,
        hospitalName: consent.hospitalName,
        doctorId: consent.doctorId,
        doctorName: consent.doctorName,
        granted: true
      });
      alert('Consent granted! The treating hospital doctor can now view your authorized health profile.');
      const user = db.getCurrentUser();
      const updated = await consentService.getConsents(user?.id);
      setConsents(updated);
    } catch (err: any) {
      console.error('Failed to grant consent:', err);
      alert(err?.message || 'Failed to grant consent on server.');
    } finally {
      setIsGranting(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* 1. WELCOME HEADER (Optimized for Mobile above-the-fold) */}
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
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Badge variant="teal">PATIENT DASHBOARD</Badge>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              ABDM Health ID: <strong>{profile.userId}</strong>
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', color: 'var(--text-heading)', margin: 0 }}>
            Welcome, {profile.fullName}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '2px 0 0' }}>
            {profile.age} yrs • {profile.gender} • Blood Group: <strong style={{ color: '#DC2626' }}>{profile.bloodGroup}</strong> • {profile.city}, Maharashtra
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <Button
            variant="danger"
            size="sm"
            onClick={onOpenEmergency}
            leftIcon={<AlertTriangle size={15} />}
          >
            Emergency 108
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenOCR}
            leftIcon={<FileText size={15} />}
          >
            Upload Rx / OCR
          </Button>
          <Button
            variant="teal"
            size="sm"
            onClick={onOpenVoiceIntake}
            leftIcon={<Mic size={15} />}
          >
            Speak Symptoms
          </Button>
        </div>
      </div>

      {/* 2. PENDING MEDICAL CONSENT ALERT (If any hospital requested records) */}
      {pendingConsent && (
        <div
          style={{
            background: 'rgba(217, 119, 6, 0.08)',
            border: '1px solid #D97706',
            borderRadius: '16px',
            padding: '16px 20px',
            marginBottom: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '8px', background: 'rgba(217, 119, 6, 0.15)', borderRadius: '10px', color: '#D97706' }}>
              <Lock size={22} />
            </div>
            <div>
              <div style={{ color: 'var(--text-heading)', fontWeight: 700, fontSize: '0.96rem' }}>
                Medical Access Consent Requested by {pendingConsent.hospitalName}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.84rem' }}>
                Attending Physician ({pendingConsent.doctorName || 'Cardiology Consultant'}) requires authorization to view your symptoms and medical record summary.
              </div>
            </div>
          </div>

          <Button
            variant="teal"
            size="sm"
            isLoading={isGranting}
            onClick={() => handleGrantConsent(pendingConsent)}
            leftIcon={<CheckCircle2 size={16} />}
          >
            Approve &amp; Grant Access
          </Button>
        </div>
      )}

      {/* 3. UPCOMING APPOINTMENT SUMMARY / EMPTY STATE */}
      <section style={{ marginBottom: '24px' }}>
        {activeOPD ? (
          <Card
            padding="20px 24px"
            style={{
              background: 'var(--bg-subtle)',
              border: '1.5px solid var(--primary-teal)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Badge variant="teal">UPCOMING OPD CONSULTATION</Badge>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary-teal)' }}>
                  REF: {activeOPD.referenceId}
                </span>
                <span className="badge badge-green" style={{ fontSize: '0.72rem' }}>
                  {activeOPD.status}
                </span>
              </div>
              <h3 style={{ fontSize: '1.3rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
                {activeOPD.hospitalName}
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>
                <Stethoscope size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                {activeOPD.doctorName} ({activeOPD.department}) • Slot: <strong>{activeOPD.appointmentDate} at {activeOPD.appointmentTime}</strong>
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <Button
                variant="secondary"
                size="sm"
                onClick={onOpenMyAppointments}
              >
                Manage Booking
              </Button>
              <Button
                variant="teal"
                size="sm"
                onClick={() => setShowQRModal(true)}
                leftIcon={<QrCode size={16} />}
              >
                View QR Digital Pass
              </Button>
            </div>
          </Card>
        ) : (
          <Card
            padding="20px 24px"
            style={{
              background: 'var(--bg-subtle)',
              border: '1px dashed var(--border-dark)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px'
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.15rem', color: 'var(--text-heading)', margin: '0 0 4px' }}>
                No Upcoming Appointments
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>
                You have no active doctor consultations scheduled. Search accredited hospitals or book an OPD slot.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <Button variant="secondary" size="sm" onClick={onOpenHospitals}>
                Find Hospitals
              </Button>
              <Button variant="teal" size="sm" onClick={onOpenBookAppointment} leftIcon={<Calendar size={15} />}>
                Book OPD Appointment
              </Button>
            </div>
          </Card>
        )}
      </section>

      {/* 4. CLINICAL CARE JOURNEY TIMELINE */}
      <CareJourneyTimeline currentStage={profile.careStage} />

      <DisclaimerBanner text="AI clinical assessments provide triage guidance and do not replace professional doctor evaluations. Severe symptoms require immediate trauma care." />

      {/* 5. PRIMARY FIVE CONNECTED SHORTCUT CARDS */}
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.35rem', color: 'var(--text-heading)', margin: 0 }}>
          Patient Services &amp; Navigation
        </h2>
        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Connected Care-to-Cost Workflow</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        {/* Shortcut 1: Check Symptoms */}
        <Card hoverable padding="20px" style={{ cursor: 'pointer' }} onClick={onOpenTriage}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(2, 132, 199, 0.12)', color: 'var(--primary-teal)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={22} />
            </div>
            <div>
              <Badge variant="teal" size="sm">CLINICAL AI</Badge>
              <h3 style={{ fontSize: '1.1rem', margin: '2px 0 0', color: 'var(--text-heading)' }}>Check Symptoms</h3>
            </div>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.45, marginBottom: '12px' }}>
            Voice and text intake with duration, severity context, and actionable triage urgency reasoning.
          </p>
          <span style={{ color: 'var(--primary-teal)', fontSize: '0.82rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            Start Triage Assessment <ArrowRight size={14} />
          </span>
        </Card>

        {/* Shortcut 2: Find Hospitals */}
        <Card hoverable padding="20px" style={{ cursor: 'pointer' }} onClick={onOpenHospitals}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(15, 23, 42, 0.08)', color: 'var(--primary-navy)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Building2 size={22} />
            </div>
            <div>
              <Badge variant="navy" size="sm">DISCOVERY</Badge>
              <h3 style={{ fontSize: '1.1rem', margin: '2px 0 0', color: 'var(--text-heading)' }}>Find Hospitals</h3>
            </div>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.45, marginBottom: '12px' }}>
            Tertiary hospitals ranked by Care Score (clinical fit, distance, fees, beds, PM-JAY empanelment).
          </p>
          <span style={{ color: 'var(--text-heading)', fontSize: '0.82rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            Explore Directory &amp; Compare <ArrowRight size={14} />
          </span>
        </Card>

        {/* Shortcut 3: My Appointments */}
        <Card hoverable padding="20px" style={{ cursor: 'pointer' }} onClick={onOpenMyAppointments}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(22, 163, 74, 0.12)', color: '#16A34A', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Calendar size={22} />
            </div>
            <div>
              <Badge variant="green" size="sm">SCHEDULE</Badge>
              <h3 style={{ fontSize: '1.1rem', margin: '2px 0 0', color: 'var(--text-heading)' }}>My Appointments</h3>
            </div>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.45, marginBottom: '12px' }}>
            View confirmed bookings, retrieve digital token QR visit passes, reschedule or cancel slots.
          </p>
          <span style={{ color: '#16A34A', fontSize: '0.82rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            View OPD Schedule &amp; QR <ArrowRight size={14} />
          </span>
        </Card>

        {/* Shortcut 4: Medical Records */}
        <Card hoverable padding="20px" style={{ cursor: 'pointer' }} onClick={onOpenHealthProfile}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(109, 40, 217, 0.12)', color: '#7C3AED', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={22} />
            </div>
            <div>
              <Badge variant="purple" size="sm">HEALTH VAULT</Badge>
              <h3 style={{ fontSize: '1.1rem', margin: '2px 0 0', color: 'var(--text-heading)' }}>Medical Records</h3>
            </div>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.45, marginBottom: '12px' }}>
            OCR prescription uploader, lab reports, past diagnoses, vitals, and consent permission controls.
          </p>
          <span style={{ color: '#7C3AED', fontSize: '0.82rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            Open Records &amp; OCR <ArrowRight size={14} />
          </span>
        </Card>

        {/* Shortcut 5: Financial Assistance */}
        <Card hoverable padding="20px" style={{ cursor: 'pointer' }} onClick={onOpenFinancialSupport}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'rgba(217, 119, 6, 0.12)', color: '#D97706', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Wallet size={22} />
            </div>
            <div>
              <Badge variant="amber" size="sm">FINANCIAL AID</Badge>
              <h3 style={{ fontSize: '1.1rem', margin: '2px 0 0', color: 'var(--text-heading)' }}>Financial Assistance</h3>
            </div>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', lineHeight: 1.45, marginBottom: '12px' }}>
            PM-JAY eligibility check, Live Care-to-Cost Calculator, and AI finance scenarios to reach ₹0 Gap.
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#D97706', fontSize: '0.82rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              Calculate Support Gap <ArrowRight size={14} />
            </span>
            <span
              onClick={(e) => { e.stopPropagation(); onOpenFinancePlanner(); }}
              style={{ fontSize: '0.74rem', color: 'var(--primary-teal)', fontWeight: 600, textDecoration: 'underline' }}
            >
              AI Planner
            </span>
          </div>
        </Card>
      </div>

      {/* 6. HEALTH PROFILE SNAPSHOT & RECENT ACTIVITY */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {/* Vitals Snapshot */}
        <Card padding="20px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h4 style={{ fontSize: '1rem', color: 'var(--text-heading)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Heart size={16} color="#DC2626" /> Active Vitals
            </h4>
            <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Updated Today</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', textAlign: 'center' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 6px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>BP</div>
              <div style={{ fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-heading)' }}>{profile.vitalSigns?.bp || '138/88'}</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 6px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>PULSE</div>
              <div style={{ fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-heading)' }}>{profile.vitalSigns?.pulse || '84 bpm'}</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 6px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>SPO2</div>
              <div style={{ fontSize: '0.96rem', fontWeight: 700, color: '#16A34A' }}>{profile.vitalSigns?.spo2 || '97%'}</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '10px 6px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>TEMP</div>
              <div style={{ fontSize: '0.96rem', fontWeight: 700, color: 'var(--text-heading)' }}>{profile.vitalSigns?.temp || '98.4°F'}</div>
            </div>
          </div>
        </Card>

        {/* Active Medications & Allergies */}
        <Card padding="20px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h4 style={{ fontSize: '1rem', color: 'var(--text-heading)', margin: 0 }}>
              Active Medications &amp; Allergies
            </h4>
            <Button variant="ghost" size="sm" onClick={onOpenHealthProfile} style={{ padding: '0 6px', fontSize: '0.78rem' }}>
              Edit
            </Button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.84rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-light)', paddingBottom: '6px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Current Rx:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-heading)' }}>
                {profile.medications.join(', ') || 'Metformin 500mg, Telmisartan 40mg'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Known Allergies:</span>
              <span style={{ fontWeight: 600, color: '#DC2626' }}>
                {profile.allergies.join(', ') || 'Penicillin'}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Digital QR Modal */}
      {showQRModal && activeOPD && (
        <div className="modal-overlay" onClick={() => setShowQRModal(false)}>
          <div className="modal-content" style={{ maxWidth: '640px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ margin: 0, color: 'var(--text-heading)' }}>Digital OPD QR Visit Pass</h3>
              <button
                onClick={() => setShowQRModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.4rem' }}
              >
                ✕
              </button>
            </div>
            <HospitalPassQR
              opd={activeOPD}
            />
          </div>
        </div>
      )}
    </div>
  );
};
