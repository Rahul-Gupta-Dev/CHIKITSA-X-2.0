import React, { useState, useEffect } from 'react';
import { db } from '../../db/database';
import { qrService, opdService, consentService } from '../../services/apiServices';
import type { OPDRegistration, PatientConsent } from '../../types';
import {
  QrCode,
  Search,
  CheckCircle2,
  AlertCircle,
  Building2,
  Lock,
  Camera,
  Activity,
  Users,
  Clock,
  BarChart3,
  ShieldCheck,
  Plus
} from 'lucide-react';
import { Button, Card, Badge } from '../common/UIComponents';
import { QRCameraScannerModal } from './QRCameraScannerModal';

interface Props {
  onConsentRequested?: () => void;
}

export const HospitalAdminDashboard: React.FC<Props> = ({ onConsentRequested }) => {
  const currentUser = db.getCurrentUser();
  const currentHospitalId = currentUser?.hospitalId || 'hosp-1';
  const hospital = db.getHospitals().find(h => h.id === currentHospitalId) || db.getHospitals()[0];
  const hospitalDoctors = db.getDoctors(hospital.id);

  const [appointments, setAppointments] = useState<OPDRegistration[]>([]);
  const [isLoadingAppointments, setIsLoadingAppointments] = useState<boolean>(true);

  const [activeTab, setActiveTab] = useState<'DASHBOARD' | 'CHECKIN' | 'DOCTORS' | 'OPD_SLOTS' | 'REPORTS' | 'PROFILE'>('CHECKIN');

  const [inputRefId, setInputRefId] = useState<string>('CHX-2026-8A92F');
  const [verificationResult, setVerificationResult] = useState<{ success: boolean; opd?: OPDRegistration; message: string } | null>(null);
  const [activeConsent, setActiveConsent] = useState<PatientConsent | null>(null);
  const [isCameraScannerOpen, setIsCameraScannerOpen] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const fetchHospitalAppointments = async () => {
    setIsLoadingAppointments(true);
    try {
      const data = await opdService.getAppointments({ hospitalId: currentHospitalId });
      setAppointments(data);
      if (data.length > 0) {
        setInputRefId(prev => prev === 'CHX-2026-8A92F' ? data[0].referenceId : prev);
      }
    } catch (err: any) {
      console.error('Failed to load hospital appointments:', err);
      setAppointments(db.getOPDRegistrations());
    } finally {
      setIsLoadingAppointments(false);
    }
  };

  useEffect(() => {
    fetchHospitalAppointments();
  }, []);

  const [isRequestingConsent, setIsRequestingConsent] = useState(false);

  const handleVerify = async (targetId?: string) => {
    const queryId = (targetId || inputRefId).trim();
    if (!queryId) return;

    setIsVerifying(true);
    try {
      const staffName = currentUser?.name || 'Reception Desk Staff';
      const res = await qrService.verifyPass(queryId, staffName);
      setVerificationResult(res);

      if (res.success && res.opd) {
        try {
          const consents = await consentService.getConsents(res.opd.patientId);
          const existing = consents.find(c => c.hospitalId === res.opd?.hospitalId || c.patientId === res.opd?.patientId);
          if (existing) setActiveConsent(existing);
          else setActiveConsent(null);
        } catch {
          const consents = db.getConsents();
          const existing = consents.find(c => c.patientId === res.opd?.patientId && c.hospitalId === res.opd?.hospitalId);
          if (existing) setActiveConsent(existing);
          else setActiveConsent(null);
        }
      } else {
        setActiveConsent(null);
      }
      await fetchHospitalAppointments();
    } finally {
      setIsVerifying(false);
    }
  };

  const handleCameraScanSuccess = (scannedId: string) => {
    setInputRefId(scannedId);
    handleVerify(scannedId);
  };

  const handleRequestConsentClick = async () => {
    if (verificationResult?.opd) {
      setIsRequestingConsent(true);
      try {
        const c = await consentService.grantConsent({
          patientId: verificationResult.opd.patientId,
          hospitalId: verificationResult.opd.hospitalId,
          hospitalName: verificationResult.opd.hospitalName,
          doctorId: verificationResult.opd.doctorId,
          doctorName: verificationResult.opd.doctorName,
          granted: false
        });
        setActiveConsent(c);
        if (onConsentRequested) onConsentRequested();
        alert('Medical record consent access request dispatched to patient dashboard!');
      } catch (err: any) {
        alert(err?.message || 'Failed to dispatch consent request.');
      } finally {
        setIsRequestingConsent(false);
      }
    }
  };

  return (
    <div style={{ maxWidth: '1150px', margin: '0 auto', padding: '10px 0 40px' }}>
      {/* Header Banner */}
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
              background: 'rgba(22, 163, 74, 0.12)',
              color: '#16A34A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Building2 size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
              <Badge variant="green">HOSPITAL ADMINISTRATION</Badge>
              <span className="badge badge-teal" style={{ fontSize: '0.72rem' }}>
                <ShieldCheck size={12} /> NABH ACCREDITED • CODE: {hospital.code}
              </span>
            </div>
            <h1 style={{ fontSize: '1.6rem', color: 'var(--text-heading)', margin: 0 }}>
              {hospital.name}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '2px 0 0' }}>
              Reception Desk &amp; Patient Check-in Terminal • {hospital.address}, {hospital.city}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Button
            variant="teal"
            size="sm"
            onClick={() => setIsCameraScannerOpen(true)}
            leftIcon={<Camera size={15} />}
          >
            Open Web Camera Scanner
          </Button>
        </div>
      </div>

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
          onClick={() => setActiveTab('CHECKIN')}
          className={`btn btn-sm ${activeTab === 'CHECKIN' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <QrCode size={15} /> QR Check-in Terminal
        </button>
        <button
          onClick={() => setActiveTab('DASHBOARD')}
          className={`btn btn-sm ${activeTab === 'DASHBOARD' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Activity size={15} /> Hospital Dashboard &amp; Beds
        </button>
        <button
          onClick={() => setActiveTab('DOCTORS')}
          className={`btn btn-sm ${activeTab === 'DOCTORS' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Users size={15} /> Doctors &amp; Staff ({hospitalDoctors.length})
        </button>
        <button
          onClick={() => setActiveTab('OPD_SLOTS')}
          className={`btn btn-sm ${activeTab === 'OPD_SLOTS' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Clock size={15} /> OPD &amp; Slot Management
        </button>
        <button
          onClick={() => setActiveTab('REPORTS')}
          className={`btn btn-sm ${activeTab === 'REPORTS' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <BarChart3 size={15} /> Analytics &amp; Reports
        </button>
        <button
          onClick={() => setActiveTab('PROFILE')}
          className={`btn btn-sm ${activeTab === 'PROFILE' ? 'btn-primary' : 'btn-ghost'}`}
        >
          <Building2 size={15} /> Hospital Profile
        </button>
      </div>

      {/* TAB 1: QR CHECK-IN TERMINAL */}
      {activeTab === 'CHECKIN' && (
        <div>
          <Card padding="28px" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', color: 'var(--text-heading)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <QrCode size={22} color="var(--primary-teal)" />
                  Scan Patient QR or Enter Reference ID
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '2px 0 0' }}>
                  Validate digital OPD visit passes, verify reference tokens, and initiate check-in.
                </p>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCameraScannerOpen(true)}
                leftIcon={<Camera size={14} />}
              >
                Launch QR Camera
              </Button>
            </div>

            {/* Input Bar */}
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
              <div style={{ flex: 1, minWidth: '260px' }}>
                <input
                  type="text"
                  value={inputRefId}
                  onChange={e => setInputRefId(e.target.value)}
                  placeholder="Enter Reference ID (e.g. CHX-2026-8A92F)..."
                  className="form-control"
                  style={{ textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}
                />
              </div>
              <Button
                variant="teal"
                isLoading={isVerifying}
                onClick={() => handleVerify()}
                leftIcon={<Search size={15} />}
              >
                Verify &amp; Check-In
              </Button>
            </div>

            {/* Recent Scheduled Registrations Quick Buttons */}
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Quick Click From Today's Bookings:
              </span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {isLoadingAppointments ? (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Loading live bookings...</span>
                ) : appointments.slice(0, 3).map(app => (
                  <button
                    key={app.id}
                    type="button"
                    onClick={() => {
                      setInputRefId(app.referenceId);
                      handleVerify(app.referenceId);
                    }}
                    style={{
                      background: inputRefId === app.referenceId ? 'rgba(2, 132, 199, 0.12)' : 'var(--bg-subtle)',
                      border: inputRefId === app.referenceId ? '1.5px solid var(--primary-teal)' : '1px solid var(--border-light)',
                      borderRadius: '8px',
                      padding: '6px 12px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: 'var(--text-heading)',
                      cursor: 'pointer'
                    }}
                  >
                    {app.patientName} — <strong>{app.referenceId}</strong>
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Verification Results Panel */}
          {verificationResult && (
            <Card
              padding="28px"
              style={{
                background: verificationResult.success ? 'rgba(22, 163, 74, 0.04)' : 'rgba(220, 38, 38, 0.04)',
                border: `1.5px solid ${verificationResult.success ? '#16A34A' : '#DC2626'}`,
                marginBottom: '24px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div
                  style={{
                    padding: '8px',
                    borderRadius: '10px',
                    background: verificationResult.success ? 'rgba(22, 163, 74, 0.15)' : 'rgba(220, 38, 38, 0.15)',
                    color: verificationResult.success ? '#16A34A' : '#DC2626'
                  }}
                >
                  {verificationResult.success ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />}
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--text-heading)' }}>
                    {verificationResult.success ? 'OPD Visit Pass Verified ✓' : 'Invalid or Expired Pass'}
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {verificationResult.message}
                  </p>
                </div>
              </div>

              {verificationResult.opd && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                  <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PATIENT NAME</span>
                    <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>
                      {verificationResult.opd.patientName}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{verificationResult.opd.patientPhone}</span>
                  </div>

                  <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CONSULTANT &amp; ROOM</span>
                    <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>
                      {verificationResult.opd.doctorName}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--primary-teal)' }}>{verificationResult.opd.department} (Room 204)</span>
                  </div>

                  <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SCHEDULED TIME</span>
                    <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>
                      {verificationResult.opd.appointmentDate}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{verificationResult.opd.appointmentTime}</span>
                  </div>

                  <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PAYMENT STATUS</span>
                    <div style={{ fontWeight: 700, color: '#16A34A', marginTop: '2px' }}>
                      ₹{verificationResult.opd.consultationFee} (Cash / PM-JAY)
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Pay at Counter</span>
                  </div>
                </div>
              )}

              {/* Patient Consent Protocol Section */}
              {verificationResult.success && verificationResult.opd && (
                <div
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-light)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Lock size={20} color="var(--primary-teal)" />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-heading)' }}>
                        Patient Medical History Consent: {activeConsent ? activeConsent.status : 'NOT REQUESTED'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Request authorization to unlock previous prescriptions, allergies, and AI triage data for the treating doctor.
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="teal"
                    size="sm"
                    disabled={activeConsent?.status === 'GRANTED' || isRequestingConsent}
                    onClick={handleRequestConsentClick}
                  >
                    {isRequestingConsent ? 'Requesting...' : activeConsent?.status === 'GRANTED' ? '✓ Consent Approved' : activeConsent?.status === 'PENDING' ? 'Consent Pending' : 'Request Patient Consent'}
                  </Button>
                </div>
              )}
            </Card>
          )}
        </div>
      )}

      {/* TAB 2: HOSPITAL DASHBOARD & BEDS */}
      {activeTab === 'DASHBOARD' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <Card padding="20px">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                General Ward Beds
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-heading)', marginTop: '4px' }}>
                124 <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 150</span>
              </div>
              <span style={{ fontSize: '0.78rem', color: '#16A34A', fontWeight: 600 }}>26 Beds Free</span>
            </Card>

            <Card padding="20px">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                Critical Care ICU Beds
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-heading)', marginTop: '4px' }}>
                18 <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 25</span>
              </div>
              <span style={{ fontSize: '0.78rem', color: '#16A34A', fontWeight: 600 }}>{hospital.icuBedsFree} ICU Beds Available</span>
            </Card>

            <Card padding="20px">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                Emergency Trauma Beds
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-heading)', marginTop: '4px' }}>
                4 <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 8</span>
              </div>
              <span style={{ fontSize: '0.78rem', color: '#DC2626', fontWeight: 600 }}>{hospital.emergencyBedsFree} Emergency Bays Open</span>
            </Card>

            <Card padding="20px">
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                Today's OPD Registrations
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--primary-teal)', marginTop: '4px' }}>
                {appointments.length}
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>All departments</span>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 3: DOCTORS & STAFF */}
      {activeTab === 'DOCTORS' && (
        <Card padding="28px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: 'var(--text-heading)', margin: 0 }}>
                Hospital Consultants &amp; Medical Staff
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '2px 0 0' }}>
                Doctors currently rostered under {hospital.name}
              </p>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => alert('Physician empanelment requires medical council license verification. Please contact administration.')}
              leftIcon={<Plus size={14} />}
            >
              Add Doctor
            </Button>
          </div>

          <table className="health-table">
            <thead>
              <tr>
                <th>Doctor</th>
                <th>Specialty</th>
                <th>Roster Days</th>
                <th>Experience</th>
                <th>Rating</th>
                <th>Consultation Fee</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {hospitalDoctors.map(doc => (
                <tr key={doc.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <img src={doc.avatar} alt={doc.name} style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover' }} />
                      <div>
                        <strong>{doc.name}</strong>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{doc.qualification}</div>
                      </div>
                    </div>
                  </td>
                  <td><Badge variant="teal" size="sm">{doc.specialty}</Badge></td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {doc.availableDays && doc.availableDays.length > 0 ? doc.availableDays.join(', ') : 'Mon - Fri'}
                    </span>
                  </td>
                  <td>{doc.experienceYears}+ years</td>
                  <td>★ {doc.rating}</td>
                  <td style={{ fontWeight: 700, color: '#16A34A' }}>₹{doc.consultationFee}</td>
                  <td><Badge variant="green" size="sm">Active Duty</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* TAB 4: OPD & SLOTS */}
      {activeTab === 'OPD_SLOTS' && (
        <Card padding="28px">
          <h2 style={{ fontSize: '1.3rem', color: 'var(--text-heading)', margin: '0 0 6px' }}>
            Department OPD Capacity &amp; Slot Management
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '0 0 20px' }}>
            Standard patient quotas per department session
          </p>

          <table className="health-table">
            <thead>
              <tr>
                <th>Department</th>
                <th>Operating Hours</th>
                <th>Daily Quota</th>
                <th>Availability Status</th>
              </tr>
            </thead>
            <tbody>
              {hospital.specialties.map(spec => (
                <tr key={spec}>
                  <td><strong>{spec}</strong></td>
                  <td>09:00 AM – 05:00 PM</td>
                  <td>30 Tokens / Day</td>
                  <td><Badge variant="green" size="sm">HIGH AVAILABILITY</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* TAB 5: REPORTS & ANALYTICS */}
      {activeTab === 'REPORTS' && (
        <Card padding="28px">
          <h2 style={{ fontSize: '1.3rem', color: 'var(--text-heading)', margin: '0 0 6px' }}>
            Facility Analytics &amp; Verified Check-ins
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '0 0 20px' }}>
            Summary of patient visits, token validation rates, and scheme utilization
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>CHECK-IN VERIFICATION RATE</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#16A34A', marginTop: '4px' }}>98.4%</div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Average check-in time: 42 seconds</span>
            </div>

            <div style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>PM-JAY SUBSIDY PROCESSED</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--primary-teal)', marginTop: '4px' }}>₹14,50,000</div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Across 18 inpatient claims this month</span>
            </div>

            <div style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>EMERGENCY TRAUMA FOOTFALL</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#DC2626', marginTop: '4px' }}>12 Patients / Day</div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>24/7 ICU triage operational</span>
            </div>
          </div>
        </Card>
      )}

      {/* TAB 6: HOSPITAL PROFILE */}
      {activeTab === 'PROFILE' && (
        <Card padding="28px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: 'var(--text-heading)', margin: 0 }}>
                {hospital.name} Facility Details
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '2px 0 0' }}>
                ABDM Facility Registration ID: <strong>IN-MH-PUN-00918</strong>
              </p>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => alert('Facility accreditation and address edits are governed by statutory health authorities.')}
            >
              Request Profile Update
            </Button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px', fontSize: '0.9rem' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>ACCREDITATION</span>
              <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>{hospital.accreditation.join(', ')}</div>
            </div>

            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>TELEPHONE HELPLINE</span>
              <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>{hospital.phone}</div>
            </div>

            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>EMERGENCY TRAUMA HOTLINE</span>
              <div style={{ fontWeight: 700, color: '#DC2626', marginTop: '2px' }}>{hospital.emergencyPhone}</div>
            </div>

            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>ADDRESS</span>
              <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginTop: '2px' }}>{hospital.address}, {hospital.city}</div>
            </div>
          </div>
        </Card>
      )}

      {/* QR Camera Scanner Modal */}
      <QRCameraScannerModal
        isOpen={isCameraScannerOpen}
        onClose={() => setIsCameraScannerOpen(false)}
        onScanSuccess={handleCameraScanSuccess}
      />
    </div>
  );
};
